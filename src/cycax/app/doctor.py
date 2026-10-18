# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""`cycax doctor`: check the tools and the server, with a fix for each problem."""

import importlib.metadata
import importlib.util
import platform
from dataclasses import dataclass
from pathlib import Path

from cycax.app.project import Project
from cycax.app.server import ServerClient
from cycax.app.tools import FreeCADLocalTool, OpenSCADTool


@dataclass
class Check:
    name: str
    status: str  # "ok", "problem" or "warning"
    detail: str = ""
    fix: str = ""


def _version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return ""


def _sheetmetal_installed() -> bool:
    folders = [Path("~/.local/share/FreeCAD/Mod"), Path("~/.FreeCAD/Mod"), Path("~/AppData/Roaming/FreeCAD/Mod")]
    return any((folder.expanduser() / name).is_dir() for folder in folders for name in ("sheetmetal", "SheetMetal"))


def _folder_size(folder: Path) -> int:
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file()) if folder.is_dir() else 0


def run_checks(project: Project, *, check_server: bool = True) -> list[Check]:
    settings = project.settings
    checks = [Check("Python", "ok", platform.python_version())]

    if importlib.util.find_spec("build123d"):
        checks.append(Check("build123d", "ok", f"{_version('build123d')} (fast local builds)"))
    else:
        checks.append(Check("build123d", "problem", "not installed", "Install cycax again (hatch env)."))

    freecad = FreeCADLocalTool(settings.tools.get("freecad")).binary()
    server_note = "builds use the server" if settings.backend != "local" else "needed for FCStd and sheet metal"
    if freecad:
        checks.append(Check("FreeCAD", "ok", str(freecad)))
        if _sheetmetal_installed():
            checks.append(Check("SheetMetal workbench", "ok", "installed"))
        else:
            checks.append(
                Check(
                    "SheetMetal workbench",
                    "problem",
                    "needed for sheet-metal parts",
                    "In FreeCAD, open Tools > Addon manager and install SheetMetal.",
                )
            )
    else:
        checks.append(
            Check("FreeCAD", "warning", f"not found; {server_note}", "Install FreeCAD 1.1 if you need it locally.")
        )

    openscad = OpenSCADTool(settings.tools.get("openscad")).binary()
    checks.append(
        Check("OpenSCAD", "ok", str(openscad))
        if openscad
        else Check("OpenSCAD", "warning", "not found (only needed for SCAD output)")
    )

    if check_server:
        client = ServerClient(settings.server_url)
        if client.available():
            checks.append(Check("Server", "ok", settings.server_url))
        else:
            status = "problem" if settings.backend == "server" else "warning"
            checks.append(
                Check("Server", status, f"{settings.server_url} not reachable", "Check [server] url in cycax.toml.")
            )

    cache = Path(settings.cache_folder).expanduser()
    checks.append(Check("Cache", "ok", f"{cache} ({_folder_size(cache) / 1e6:.1f} MB)"))
    if not project.has_project_file:
        checks.append(Check("Project", "warning", "no cycax.toml here or in a parent folder", "Run: cycax init"))
    else:
        checks.append(Check("Project", "ok", str(project.root / "cycax.toml")))
    return checks
