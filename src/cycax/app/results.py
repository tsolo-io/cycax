# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Where results are, and opening them with the right application or editor."""

import os
import platform
import shlex
import shutil
import subprocess
from pathlib import Path

from cycax.app.errors import TargetNotFoundError, ToolMissingError
from cycax.app.project import Project

# The default result to open, in order of preference.
OPEN_ORDER = ("fcstd", "step", "stl", "glb", "dxf", "scad")


def result_files(project: Project, target: str) -> dict[str, Path]:
    """The files of a built target in the build folder (format -> path)."""
    folder = project.build_folder / target
    files = {}
    if folder.is_dir():
        for path in sorted(folder.iterdir()):
            if path.name.endswith("_drawing.svg"):
                files["drawing"] = path
                continue
            if path.name.endswith("_views.png"):
                files["views"] = path
                continue
            if path.name.endswith("_summary.json"):
                files["summary"] = path
                continue
            if path.suffix.lower() in {".json", ".log"}:
                continue
            fmt = "dxf" if path.name.endswith("_unfold.dxf") else path.suffix.lstrip(".").lower()
            files[fmt] = path
    return files


def pick_result(project: Project, target: str, fmt: str | None = None) -> Path:
    files = result_files(project, target)
    if fmt:
        if fmt not in files:
            msg = f"{target} has no {fmt} result."
            raise TargetNotFoundError(msg, fix=f"cycax build {target} --output {fmt}")
        return files[fmt]
    for candidate in OPEN_ORDER:
        if candidate in files:
            return files[candidate]
    msg = f"{target} is not built yet."
    raise TargetNotFoundError(msg, fix=f"cycax build {target}")


def open_path(path: Path):
    """Open a file or folder with the system default application."""
    system = platform.system()
    if system == "Windows":  # pragma: no cover
        os.startfile(path)  # noqa: S606
        return
    opener = "open" if system == "Darwin" else "xdg-open"
    if not shutil.which(opener):
        msg = f"Cannot open files here ({opener} is not installed)."
        raise ToolMissingError(msg, fix=f"Open it yourself: {path}")
    subprocess.Popen([opener, str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603


def editor_command(project: Project, file: Path, line: int = 1) -> list[str]:
    """The command to open `file` at `line`: the user setting (e.g. "zed {file}:{line}" or
    "code -g {file}:{line}"), else $VISUAL, $EDITOR, then vi with +line."""
    template = project.settings.editor
    if template:
        return [part.format(file=file, line=line) for part in shlex.split(template)]
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
    return [*shlex.split(editor), f"+{line}", str(file)]
