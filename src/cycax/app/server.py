# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The CLI's NATS client (task cycax/16), per cycax-server docs/content/nats-protocol.md.

Flow for one (hash, worker, formats, profile):
1. Look in the NATS cache (Object Store `cycax_cache`) for each format at or above the profile.
2. Missing formats: if `cycax_pending` has `<hash>.<worker>.<profile>` (someone else is
   building it) and not `force`, wait for the files; else write the pending marker, write
   `<hash>/spec.json`, publish the task to `cycax.tasks.<worker>` with a reply subject, and wait.
3. The cache is the source of truth: waiting means "reply or cache poll, whichever first".
4. Download the best file of each format.

Each public method runs its own short asyncio session, so the builder stays synchronous.
"""

import asyncio
import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from cycax import quality
from cycax.app.errors import BuildFailedError, ServerUnavailableError

CACHE_BUCKET = "cycax_cache"
META_BUCKET = "cycax_meta"
PENDING_BUCKET = "cycax_pending"
QUALITY_BUCKET = "cycax_quality"
CLIENT_ID = uuid.uuid4().hex[:12]


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


class ServerClient:
    def __init__(self, url: str, *, connect_timeout: float = 2.0, wait_timeout: float = 3600.0):
        self.url = url
        self.connect_timeout = connect_timeout
        self.wait_timeout = wait_timeout
        self._available: bool | None = None

    # -- connection -----------------------------------------------------------------------
    async def _connect(self):
        import nats  # noqa: PLC0415

        try:
            # max_reconnect_attempts also bounds the first connect (nats-py retries it).
            return await nats.connect(self.url, connect_timeout=self.connect_timeout, max_reconnect_attempts=1)
        except Exception as error:  # noqa: BLE001
            msg = f"The CyCAx server (NATS) at {self.url} is not reachable: {error}"
            raise ServerUnavailableError(msg, fix="Check [server] url in cycax.toml, or build with --local.") from None

    def available(self) -> bool:
        if self._available is None:

            async def probe():
                nc = await self._connect()
                await nc.close()

            try:
                asyncio.run(probe())
                self._available = True
            except ServerUnavailableError:
                self._available = False
        return self._available

    async def _object_store(self, js):
        from nats.js.errors import BucketNotFoundError  # noqa: PLC0415

        try:
            return await js.object_store(CACHE_BUCKET)
        except BucketNotFoundError:
            return await js.create_object_store(CACHE_BUCKET)

    async def _kv(self, js, bucket: str):
        from nats.js.errors import BucketNotFoundError  # noqa: PLC0415

        try:
            return await js.key_value(bucket)
        except BucketNotFoundError:
            return await js.create_key_value(bucket=bucket)

    # -- quality table --------------------------------------------------------------------
    async def _scores(self, js) -> dict[str, int]:
        """The live score table; seeds KV `cycax_quality` from the defaults when it is empty."""
        from nats.js.errors import NoKeysError  # noqa: PLC0415

        kv = await self._kv(js, QUALITY_BUCKET)
        try:
            keys = await kv.keys()
        except NoKeysError:
            keys = []
        if not keys:
            for key, score in quality.DEFAULT_SCORES.items():
                await kv.put(key, json.dumps({"score": score}).encode())
            return dict(quality.DEFAULT_SCORES)
        scores = {}
        for key in keys:
            entry = await kv.get(key)
            try:
                scores[key] = int(json.loads(entry.value)["score"])
            except (ValueError, KeyError, TypeError):
                continue
        return scores

    def scores(self) -> dict[str, int]:
        async def run():
            nc = await self._connect()
            try:
                return await self._scores(nc.jetstream())
            finally:
                await nc.close()

        return asyncio.run(run())

    # -- cache ----------------------------------------------------------------------------
    @staticmethod
    async def _hash_files(store, cache_hash: str) -> list[str]:
        prefix = f"{cache_hash}/"
        try:
            objects = await store.list(ignore_deletes=True)
        except Exception:  # noqa: BLE001 - empty store
            return []
        return [obj.name[len(prefix) :] for obj in objects if obj.name.startswith(prefix)]

    @staticmethod
    def _missing(files: list[str], formats: list[str], profile: str, scores: dict[str, int]) -> list[str]:
        return [f for f in formats if quality.select_best(files, f, table=scores, min_profile=profile) is None]

    async def _touch(self, js, cache_hash: str):
        """Update `accessed_at` (LRU) when a cached file is used."""
        from nats.js.errors import KeyNotFoundError  # noqa: PLC0415

        kv = await self._kv(js, META_BUCKET)
        try:
            entry = await kv.get(cache_hash)
        except KeyNotFoundError:
            return
        meta = json.loads(entry.value) if entry.value else {}
        meta["accessed_at"] = _now()
        await kv.put(cache_hash, json.dumps(meta).encode())

    def fetch(
        self,
        *,
        spec: dict,
        cache_hash: str,
        worker: str,
        formats: list[str],
        profile: str,
        out_dir: Path,
        editable: bool = False,
        force: bool = False,
        on_progress=None,
        source_files: dict[str, Path] | None = None,
        inputs: dict | None = None,
    ) -> dict[str, Path]:
        """Get `formats` for one spec from the server: from the cache, or build it. Returns
        format -> downloaded file (named `<artifact name>` in `out_dir`). `source_files`: an
        imported part's model file, put in the cache for the worker (cycax/35)."""
        return asyncio.run(
            self._fetch(
                spec, cache_hash, worker, formats, profile, out_dir, editable, force, on_progress, source_files, inputs
            )
        )

    async def _fetch(
        self,
        spec,
        cache_hash,
        worker,
        formats,
        profile,
        out_dir,
        editable,
        force,
        on_progress,
        source_files=None,
        inputs=None,
    ):
        nc = await self._connect()
        try:
            js = nc.jetstream()
            store = await self._object_store(js)
            scores = await self._scores(js)
            files = await self._hash_files(store, cache_hash)
            missing = self._missing(files, formats, profile, scores) if not force else list(formats)
            if missing:
                await self._upload_import(store, spec, cache_hash, files, source_files)
                await self._upload_inputs(store, inputs)
                await self._request(
                    nc, js, store, spec, cache_hash, worker, missing, profile, editable, force, on_progress
                )
                files = await self._hash_files(store, cache_hash)
                still = self._missing(files, formats, profile, scores)
                if still:
                    msg = f"The {worker} worker did not produce {', '.join(still)} for {spec.get('name')}."
                    raise BuildFailedError(msg, fix=f"See the log in the cache: {cache_hash}/<name>-{worker}.log")
            else:
                await self._touch(js, cache_hash)
            out_dir.mkdir(parents=True, exist_ok=True)
            result = {}
            for fmt in formats:
                best = quality.select_best(files, fmt, table=scores, min_profile=profile)
                obj = await store.get(f"{cache_hash}/{best}")
                target = out_dir / best
                target.write_bytes(obj.data)
                result[fmt] = target
            return result
        finally:
            await nc.close()

    async def _upload_inputs(self, store, inputs):
        """An assembly's part files that are only in the LOCAL cache (a part built here before):
        put them in the server cache, so the assembly worker finds them (it would wait forever)."""
        for part_hash, files in (inputs or {}).items():
            on_server = set(await self._hash_files(store, part_hash))
            for file in files.values():
                local = Path(file)
                if local.name not in on_server:
                    await store.put(f"{part_hash}/{local.name}", local.read_bytes())

    @staticmethod
    async def _upload_import(store, spec, cache_hash, files, source_files):
        """Put an imported part's model file in the cache as `<hash>/<name>-import.<format>`."""
        from cycax.cycad.imported import import_object_name  # noqa: PLC0415

        object_name = import_object_name(spec)
        if object_name is None or object_name in files:
            return
        base = spec["features"][0]
        path = (source_files or {}).get(base["file"])
        if path is None:
            msg = f"{spec['name']}: the model file {base['file']} is not on this computer."
            raise BuildFailedError(msg, fix="Build it in the project that has the file.")
        await store.put(f"{cache_hash}/{object_name}", Path(path).read_bytes())

    async def _request(self, nc, js, store, spec, cache_hash, worker, formats, profile, editable, force, on_progress):
        from nats.js.errors import KeyNotFoundError  # noqa: PLC0415

        pending = await self._kv(js, PENDING_BUCKET)
        key = f"{cache_hash}.{worker}.{profile}"
        in_flight = False
        if not force:
            try:
                await pending.get(key)
                in_flight = True
            except KeyNotFoundError:
                in_flight = False
        reply_subject = f"cycax.reply.{CLIENT_ID}.{uuid.uuid4().hex[:8]}"
        sub = await nc.subscribe(reply_subject)
        try:
            if in_flight:
                if on_progress:
                    on_progress(f"already building on {worker}, waiting")
            else:
                await pending.put(key, json.dumps({"state": "PENDING", "since": _now()}).encode())
                await store.put(f"{cache_hash}/spec.json", json.dumps(spec).encode())
                task = {
                    "hash": cache_hash,
                    "kind": spec.get("kind", "part"),
                    "name": spec.get("name", cache_hash),
                    "formats": formats,
                    "profile": profile,
                    "editable": editable,
                    "reply_to": reply_subject,
                    "force": force,
                    "requested_at": _now(),
                }
                await js.publish(f"cycax.tasks.{worker}", json.dumps(task).encode())
                if on_progress:
                    on_progress(f"sent to the {worker} worker")
            await self._wait(sub, store, cache_hash, formats, profile, worker, on_progress)
        finally:
            await sub.unsubscribe()

    async def _wait(self, sub, store, cache_hash, formats, profile, worker, on_progress):
        """Wait for a reply or for the files to appear in the cache, whichever comes first."""
        import nats.errors  # noqa: PLC0415

        deadline = time.monotonic() + self.wait_timeout
        scores = None
        while time.monotonic() < deadline:
            try:
                msg = await sub.next_msg(timeout=5.0)
                result = json.loads(msg.data)
                status = result.get("status")
                if status == "completed":
                    return
                if status == "failed":
                    msg_text = f"The {worker} worker failed: {result.get('error')}"
                    raise BuildFailedError(msg_text, fix=f"See the log in the cache: {cache_hash}/<name>-{worker}.log")
                if status == "waiting" and on_progress:
                    on_progress("waiting for its inputs")
            except nats.errors.TimeoutError:
                pass
            files = await self._hash_files(store, cache_hash)
            if scores is None:
                scores = dict(quality.DEFAULT_SCORES)
            if not self._missing(files, formats, profile, scores):
                return
        msg = f"Timed out after {self.wait_timeout:.0f} s waiting for the {worker} worker."
        raise BuildFailedError(msg, fix="Check the worker with `cycax status`, or use --force to send it again.")
