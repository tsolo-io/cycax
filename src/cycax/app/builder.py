# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Plan and build targets (task cycax/14). Used by `cycax.build()`, the CLI and the UI.

For each target object (part or assembly): export the spec, plan the steps (planner.py), use
the local cache first, run the tools for what is missing, store the results in the local cache,
and copy the best file of each format into `<build folder>/<target>/`.
"""

import contextlib
import json
import logging
import os
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from cycax import quality
from cycax.app import planner
from cycax.app.cache import LocalCache
from cycax.app.errors import CycaxError, user_code_error
from cycax.app.events import Event, TargetDone, TargetFailed, TargetProgress, TargetStarted
from cycax.app.project import Project
from cycax.app.server import ServerClient
from cycax.app.tools import local_tools, scratch_dir, server_tools
from cycax.spec import spec_hash

# What an assembly engine needs from its parts.
ASSEMBLY_INPUT = {"build123d": "step", "freecad": "step", "blender": "stl", "openscad": "stl"}


@dataclass
class BuildItem:
    """One part or assembly object to build, and the target it came from."""

    target: str
    obj: object  # CycadPart or Assembly
    engine: str | None = None  # per-target engine (decorator), engine-selection.md rule 2


@dataclass
class TargetResult:
    name: str
    kind: str
    files: dict[str, Path] = field(default_factory=dict)
    cached: bool = False
    error: str | None = None
    fix: str | None = None
    seconds: float = 0.0
    exit_code: int = 0  # CLI exit code of the error (errors.py)


@dataclass
class BuildResult:
    targets: dict[str, TargetResult] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(result.error is None for result in self.targets.values())

    @property
    def files(self) -> dict[str, Path]:
        """All result files of a one-target build (format -> path)."""
        merged = {}
        for result in self.targets.values():
            merged.update(result.files)
        return merged


@dataclass
class PlannedSpec:
    name: str
    kind: str
    spec: dict
    cache_hash: str
    steps: list[planner.Step]
    cached: dict[str, Path] = field(default_factory=dict)  # format -> cached file
    source_files: dict[str, Path] = field(default_factory=dict)  # imported model files (cycax/35)


class Builder:
    def __init__(
        self,
        project: Project,
        *,
        backend: str | None = None,
        profile: str | None = None,
        outputs: list[str] | None = None,
        force: bool = False,
        editable: bool = False,
        on_event: Callable[[Event], None] | None = None,
        server_client: ServerClient | None = None,
        jobs: int | None = None,
    ):
        self.project = project
        settings = project.settings
        self.backend = backend or settings.backend
        self.profile = profile or settings.profile
        self.outputs = outputs
        self.force = force
        self.editable = editable
        self.on_event = on_event or (lambda _event: None)
        self.cache = LocalCache(settings.cache_folder)
        self.client = server_client or ServerClient(settings.server_url)
        self.local = local_tools(settings.tools)
        self.server = server_tools(self.client)
        self.table = dict(settings.quality)
        # Parallel local builds: None = the project setting, else all cores; 1 = one at a time.
        self.jobs = jobs if jobs is not None else settings.jobs
        # Results of the parallel pre-build, by cache hash: the serial pass uses them instead of
        # building again (also with --force) and reports a pool failure without a second try.
        self._prebuilt: dict[str, dict[str, Path]] = {}
        self._prebuild_errors: dict[str, BaseException] = {}

    # -- planning -------------------------------------------------------------------------
    def plan_object(self, obj, *, engine: str | None = None, outputs: list[str] | None = None) -> PlannedSpec:
        spec = obj.export()
        planned = PlannedSpec(
            name=spec["name"],
            kind=spec["kind"],
            spec=spec,
            cache_hash=spec_hash(spec),
            source_files=dict(getattr(obj, "source_files", {}) or {}),
            steps=planner.plan_spec(
                spec,
                outputs=outputs if outputs is not None else self.outputs,
                project_outputs=self.project.settings.outputs,
                project_engine=self.project.settings.engine,
                target_engine=engine,
                backend=self.backend,
                local=self.local,
                server=self.server,
            ),
        )
        if not self.force:
            for step in planned.steps:
                for fmt in step.formats:
                    found = self.cache.find(planned.cache_hash, fmt, min_profile=self.profile, table=self.table)
                    if found:
                        planned.cached[fmt] = found
        return planned

    def plan_parts(self, assembly, assembly_plan: PlannedSpec) -> list[tuple[object, PlannedSpec]]:
        """Plans for the parts an assembly needs, in the format its engine reads."""
        needs = sorted({ASSEMBLY_INPUT[step.engine] for step in assembly_plan.steps})
        flattened = assembly.combine_all_assemblies() if assembly.assemblies else assembly
        seen, plans = set(), []
        for part in flattened.parts.values():
            part_plan = self.plan_object(part, outputs=needs)
            if part_plan.cache_hash not in seen:
                seen.add(part_plan.cache_hash)
                plans.append((part, part_plan))
        return plans

    # -- building -------------------------------------------------------------------------
    def _run(self, planned: PlannedSpec, target: str, inputs: dict | None = None) -> dict[str, Path]:
        """Make the missing formats of one spec; returns format -> cached file."""
        if planned.cache_hash in self._prebuild_errors:
            raise self._prebuild_errors[planned.cache_hash]
        self.cache.put_spec(planned.cache_hash, planned.spec)
        result = {**planned.cached, **self._prebuilt.get(planned.cache_hash, {})}
        work = scratch_dir()
        try:
            for step in planned.steps:
                missing = [fmt for fmt in step.formats if fmt not in result]
                if not missing:
                    continue
                where = "on the server" if step.where == "server" else "locally"
                self.on_event(TargetProgress(target, f"{planned.name}: {step.engine} {where} ({', '.join(missing)})"))
                start = time.monotonic()
                produced = step.tool.build(
                    kind=planned.kind,
                    spec=planned.spec,
                    cache_hash=planned.cache_hash,
                    work_dir=work,
                    formats=missing,
                    profile=self.profile,
                    editable=self.editable,
                    force=self.force,
                    inputs=inputs,
                    source_files=planned.source_files,
                    on_progress=lambda message: self.on_event(TargetProgress(target, f"{planned.name}: {message}")),
                )
                seconds = time.monotonic() - start
                for fmt, path in produced.items():
                    artifact = quality.parse_artifact_name(path.name)
                    engine = artifact.engine if artifact and step.where == "server" else step.engine
                    profile = artifact.profile if artifact and step.where == "server" else self.profile
                    result[fmt] = self.cache.put(
                        planned.cache_hash,
                        path,
                        name=planned.name,
                        engine=engine,
                        profile=profile,
                        ext=fmt,
                        settings={"profile": self.profile, "where": step.where},
                        build_seconds=seconds,
                    )
                not_made = [fmt for fmt in missing if fmt not in produced]
                if not_made:
                    msg = f"{step.engine} did not make {', '.join(not_made)} for {planned.name}."
                    raise CycaxError(msg, fix="Run with -v to see the engine log.")
        finally:
            shutil.rmtree(work, ignore_errors=True)
        return result

    def _publish(self, target: str, planned: PlannedSpec, files: dict[str, Path]) -> dict[str, Path]:
        """Copy the result files into `<build folder>/<target>/` with plain names."""
        folder = self.project.build_folder / target
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{planned.name}.json").write_text(json.dumps(planned.spec, indent=2))
        published = {}
        for fmt, path in files.items():
            suffix = {
                "dxf": "_unfold.dxf",
                "fcstd": ".FCStd",
                "summary": "_summary.json",
                "svg": "_views.svg",
                "views": "_views.png",
                "drawing": "_drawing.svg",
            }.get(fmt, f".{fmt}")
            destination = folder / f"{planned.name}{suffix}"
            shutil.copyfile(path, destination)
            published[fmt] = destination
        return published

    def _log_handler(self, target: str) -> logging.Handler:
        """All log records of one target build go to `<build folder>/<target>/build.log`."""
        folder = self.project.build_folder / target
        folder.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(folder / "build.log", mode="w", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logging.getLogger().addHandler(handler)
        return handler

    def build_item(self, item: BuildItem) -> TargetResult:
        kind = "assembly" if hasattr(item.obj, "parts") else "part"
        result = TargetResult(name=item.target, kind=kind)
        log_handler = self._log_handler(item.target)
        self.on_event(TargetStarted(item.target, kind=kind))
        start = time.monotonic()
        try:
            planned = self.plan_object(item.obj, engine=item.engine)
            inputs = None
            all_cached = len(planned.cached) == sum(len(step.formats) for step in planned.steps)
            if kind == "assembly" and not all_cached:
                inputs = {}
                for _part, part_plan in self.plan_parts(item.obj, planned):
                    inputs[part_plan.cache_hash] = self._run(part_plan, item.target)
            elif not all_cached and any(step.engine == "blender" for step in planned.steps):
                # Blender renders a part from its STL (blender/09): make that first, by the
                # project's engine, and hand it over like an assembly's parts.
                mesh_plan = self.plan_object(item.obj, outputs=[ASSEMBLY_INPUT["blender"]])
                inputs = {planned.cache_hash: self._run(mesh_plan, item.target)}
            files = self._run(planned, item.target, inputs)
            result.files = self._publish(item.target, planned, files)
            result.cached = all_cached
            result.seconds = time.monotonic() - start
            self.on_event(
                TargetDone(item.target, kind=kind, files=result.files, cached=result.cached, seconds=result.seconds)
            )
        except Exception as error:
            logging.debug("Build of %s failed", item.target, exc_info=True)
            known = user_code_error(error, context=f"cycax build {item.target}")
            result.error, result.fix, result.exit_code = known.message, known.fix, known.exit_code
            self.on_event(TargetFailed(item.target, error=result.error, fix=result.fix))
        finally:
            logging.getLogger().removeHandler(log_handler)
            log_handler.close()
        return result

    # -- parallel pre-build (task cycax/41) ----------------------------------------------------
    def _local_jobs(self, items: list[BuildItem]) -> list[tuple]:
        """Local build123d builds of parts that are not in the cache, unique by hash."""
        jobs, seen = [], set()

        def add(planned):
            if planned.kind != "part" or planned.cache_hash in seen or planned.source_files:
                return
            for step in planned.steps:
                missing = [f for f in step.formats if f not in planned.cached]
                if missing and step.where == "local" and step.engine == "build123d":
                    seen.add(planned.cache_hash)
                    jobs.append((planned.spec, planned.cache_hash, missing, self.profile))

        for item in items:
            try:
                planned = self.plan_object(item.obj, engine=item.engine)
                add(planned)
                if planned.kind == "assembly":
                    for _part, part_plan in self.plan_parts(item.obj, planned):
                        add(part_plan)
            except Exception:  # noqa: BLE001, S112 - the normal pass reports it
                continue
        return jobs

    def _prebuild(self, items: list[BuildItem]):
        jobs = self._local_jobs(items)
        workers = self.jobs or os.cpu_count() or 1
        if len(jobs) < 2 or workers < 2:  # noqa: PLR2004
            return
        import concurrent.futures  # noqa: PLC0415

        logging.info("Building %d parts on %d cores", len(jobs), min(workers, len(jobs)))
        context = _pool_context()
        with concurrent.futures.ProcessPoolExecutor(max_workers=min(workers, len(jobs)), mp_context=context) as pool:
            with _main_script_hidden():
                futures = {pool.submit(_build_local_part, *job): job for job in jobs}
                concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in concurrent.futures.as_completed(futures):
                spec, cache_hash, _formats, _profile = futures[future]
                try:
                    produced, seconds = future.result()
                except concurrent.futures.process.BrokenProcessPool:
                    # A worker died (e.g. out of memory): the serial pass builds it again.
                    logging.debug("Parallel build of %s lost its process", spec["name"], exc_info=True)
                    continue
                except Exception as error:  # noqa: BLE001 - reported by the serial pass, not built twice
                    logging.debug("Parallel build of %s failed", spec["name"], exc_info=True)
                    self._prebuild_errors[cache_hash] = error
                    continue
                self.cache.put_spec(cache_hash, spec)
                built = self._prebuilt.setdefault(cache_hash, {})
                for fmt, path in produced.items():
                    built[fmt] = self.cache.put(
                        cache_hash,
                        Path(path),
                        name=spec["name"],
                        engine="build123d",
                        profile=self.profile,
                        ext=fmt,
                        settings={"profile": self.profile, "where": "local"},
                        build_seconds=seconds,
                    )
                for path in {Path(p).parent.parent for p in produced.values()}:
                    shutil.rmtree(path, ignore_errors=True)

    def build(self, items: list[BuildItem]) -> BuildResult:
        """Build the items, parts before assemblies (uncached local parts first in parallel)."""
        self._prebuild(items)
        ordered = sorted(items, key=lambda item: hasattr(item.obj, "parts"))
        build_result = BuildResult()
        for item in ordered:
            key = (
                item.target if item.target not in build_result.targets else f"{item.target}:{item.obj.export()['name']}"
            )
            build_result.targets[key] = self.build_item(item)
        return build_result


def _build_local_part(spec: dict, cache_hash: str, formats: list[str], profile: str) -> tuple[dict, float]:
    """One local build123d part build in a worker process (task cycax/41)."""
    from cycax.app.tools import Build123dTool  # noqa: PLC0415

    start = time.monotonic()
    produced = Build123dTool().build(
        kind="part", spec=spec, work_dir=scratch_dir(), formats=formats, profile=profile, cache_hash=cache_hash
    )
    return {fmt: str(path) for fmt, path in produced.items()}, time.monotonic() - start


def _pool_context():
    """The multiprocessing start method for the pre-build.

    Not "fork": a forked child of a process that has OCP (and logging) loaded can deadlock on a
    lock it inherits (found: the workers hung with 0 CPU time). "forkserver" (Linux, macOS)
    forks from a clean server that has build123d loaded once; Windows has only "spawn".
    """
    import multiprocessing  # noqa: PLC0415

    if "forkserver" in multiprocessing.get_all_start_methods():
        context = multiprocessing.get_context("forkserver")
        context.set_forkserver_preload(["cycax.cycad.engines.part_build123d"])
        return context
    return multiprocessing.get_context("spawn")


@contextlib.contextmanager
def _main_script_hidden():
    """New worker processes import the main script again when it has no module spec (a user
    script run as a file), and run its build again when it has no `__main__` guard. Hide it
    while the workers start: the work function is in cycax, not in the script."""
    import sys  # noqa: PLC0415

    main = sys.modules.get("__main__")
    hidden = main is not None and getattr(main, "__spec__", None) is None and hasattr(main, "__file__")
    saved = main.__file__ if hidden else None
    if hidden:
        del main.__file__
    try:
        yield
    finally:
        if hidden:
            main.__file__ = saved
