# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The public Python API: `cycax.build()`."""

import logging
from collections.abc import Callable
from pathlib import Path

from cycax.app.builder import Builder, BuildItem, BuildResult, TargetResult
from cycax.app.errors import CycaxError, user_code_error
from cycax.app.events import Event, TargetFailed
from cycax.app.project import Project
from cycax.targets import TARGET_ATTRIBUTE, load_targets


def build_items(project: Project, target) -> list[BuildItem]:
    """Turn one target reference into build items.

    `target` can be: a target name in the project ("bracket", or a unique part of it),
    "file.py:name", a decorated function or class, or a CycadPart/Assembly object.
    """
    if isinstance(target, str):
        if ":" in target or target.endswith(".py"):
            source, _, name = target.partition(":")
            targets = load_targets(source, name or None)
        else:
            targets = [project.find_target(target).target]
        return [BuildItem(t.name, obj, t.engine) for t in targets for obj in t.make()]
    marker = getattr(target, TARGET_ATTRIBUTE, None)
    if marker is not None:
        return [BuildItem(marker.name, obj, marker.engine) for obj in marker.make()]
    if isinstance(target, list | tuple):
        return [item for entry in target for item in build_items(project, entry)]
    name = getattr(target, "part_no", None) or getattr(target, "name", None) or "target"
    return [BuildItem(name, target)]


def build(
    *targets,
    outputs: list[str] | None = None,
    backend: str | None = None,
    profile: str | None = None,
    force: bool = False,
    editable: bool = False,
    project: Project | None = None,
    project_dir: Path | str | None = None,
    on_event: Callable[[Event], None] | None = None,
) -> BuildResult:
    """Build parts and assemblies, locally, on the server, or both (backend "auto").

    Args:
        targets: Target names, "file.py:name", decorated functions/classes, or part/assembly
            objects. No targets = every target in the project.
        outputs: Formats, e.g. ["step", "stl"]. None = the project default (cycax.toml).
        backend: "local", "server" or "auto". None = the project setting.
        profile: "draft", "standard" or "fine". None = the project setting.
        force: Build again, also when the result is in the cache.
        editable: FreeCAD only: keep the full parametric tree (slow).
        project: A loaded project; default: find it from `project_dir` or the current folder.
        on_event: Called with each build event (cycax.app.events).

    Returns:
        A BuildResult: per target the files (format -> path in the build folder) or the error.
        It never calls sys.exit().
    """
    project = project or Project.load(Path(project_dir) if project_dir else None)
    items, failed = collect_items(project, list(targets) or list(project.targets()), on_event=on_event)
    builder = Builder(
        project,
        backend=backend,
        profile=profile,
        outputs=outputs,
        force=force,
        editable=editable,
        on_event=on_event,
    )
    result = builder.build(items)
    result.targets = {**failed, **result.targets}
    return result


def target_label(target) -> str:
    if isinstance(target, str):
        return target.rpartition(":")[2] or target
    marker = getattr(target, TARGET_ATTRIBUTE, None)
    return marker.name if marker else getattr(target, "__name__", str(target))


def collect_items(
    project: Project, targets: list, *, on_event: Callable[[Event], None] | None = None
) -> tuple[list[BuildItem], dict[str, TargetResult]]:
    """Build items for each target. A target that cannot make its objects (an error in the user
    code) becomes a failed result, so the other targets still build. A target name that does
    not exist is a usage error and stops."""
    items, failed = [], {}
    for target in targets:
        try:
            items.extend(build_items(project, target))
        except CycaxError as error:
            if error.exit_code == 2:  # noqa: PLR2004 - usage error: stop here
                raise
            failed[target_label(target)] = _failed(target, error, on_event)
        except Exception as error:  # noqa: BLE001 - user code
            logging.debug("Target %s failed", target_label(target), exc_info=True)
            known = user_code_error(error, context=f"cycax build {target_label(target)}")
            failed[target_label(target)] = _failed(target, known, on_event)
    return items, failed


def _failed(target, error: CycaxError, on_event) -> TargetResult:
    name = target_label(target)
    if on_event:
        on_event(TargetFailed(name, error=error.message, fix=error.fix))
    return TargetResult(name=name, kind="", error=error.message, fix=error.fix, exit_code=error.exit_code)
