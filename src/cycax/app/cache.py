# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The local artifact cache (upgrade plan P1.3, task cycax/11).

Same layout as the NATS Object Store cache (cycax-server docs/content/nats-protocol.md §5):
`<root>/<hash>/<name>-<engine>-<profile>.<ext>`, plus `<root>/<hash>/spec.json`. The manifest
is `<root>/<hash>/manifest.json` (the local cache has one writer, so one file is fine; the NATS
cache uses per-object metadata instead).
"""

import json
import shutil
import time
from pathlib import Path

from cycax import quality

DEFAULT_ROOT = Path("~/.cache/cycax").expanduser()


class LocalCache:
    def __init__(self, root: Path | str | None = None):
        self.root = Path(root).expanduser() if root else DEFAULT_ROOT

    def folder(self, cache_hash: str) -> Path:
        return self.root / cache_hash

    def files(self, cache_hash: str) -> list[str]:
        folder = self.folder(cache_hash)
        return sorted(p.name for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []

    def put_spec(self, cache_hash: str, spec: dict):
        folder = self.folder(cache_hash)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "spec.json").write_text(json.dumps(spec))

    def put(
        self,
        cache_hash: str,
        source: Path,
        *,
        name: str,
        engine: str,
        profile: str,
        ext: str,
        settings: dict | None = None,
        build_seconds: float = 0.0,
    ) -> Path:
        """Copy a produced file into the cache under its artifact name; record it in the manifest."""
        level = profile if ext.lower() in {"stl", "glb", "png"} else quality.DEFAULT_PROFILE
        filename = quality.artifact_name(name, engine, level, ext)
        folder = self.folder(cache_hash)
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / filename
        shutil.copyfile(source, target)
        manifest_file = folder / "manifest.json"
        manifest = json.loads(manifest_file.read_text()) if manifest_file.exists() else {}
        manifest[filename] = {
            "engine": engine,
            "profile": level,
            "settings": settings or {},
            "build_seconds": round(build_seconds, 2),
            "created_at": time.time(),
        }
        manifest_file.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        return target

    def find(
        self, cache_hash: str, ext: str, *, min_profile: str = "draft", table: dict[str, int] | None = None
    ) -> Path | None:
        """The best cached file of one format at or above `min_profile` (score table rules)."""
        best = quality.select_best(self.files(cache_hash), ext, table=table, min_profile=min_profile)
        return self.folder(cache_hash) / best if best else None
