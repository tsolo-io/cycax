# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Engine adapters (tools) with one interface, local or on the server.

A tool builds one spec (part or assembly) into some formats at a quality profile and returns
`{format: produced file}`. The builder puts the files into the local cache.
"""

import json
import platform
import shutil
import tempfile
from pathlib import Path

from cycax.app.errors import ToolMissingError
from cycax.app.server import ServerClient

# What each engine can make (docs/content/engine-selection.md).
ENGINE_FORMATS = {
    "part": {
        "build123d": {"step", "stl", "glb", "summary", "svg"},
        "freecad": {"step", "stl", "glb", "fcstd", "dxf", "png", "drawing"},
        "openscad": {"stl", "scad"},
        "python": {"step", "stl", "glb", "summary", "svg", "png", "views"},
        "blender": {"png", "blend", "glb"},  # renders from the part's STL (blender/09)
    },
    "assembly": {
        "build123d": {"step", "stl"},
        "freecad": {"step", "stl", "fcstd"},
        "blender": {"blend", "glb", "png"},
        "openscad": {"scad"},
    },
}
# Engines that run on the server, by worker kind (a worker kind may serve only some kinds).
SERVER_WORKERS = {
    "freecad": ("freecad", {"part", "assembly"}),
    "blender": ("blender", {"part", "assembly"}),
    "python": ("python", {"part"}),
    # The python worker is the build123d worker on the server (martin, 2026-10-18).
    "build123d": ("python", {"part"}),
}


class Tool:
    engine = ""
    where = "local"
    kinds: frozenset[str] = frozenset()

    def available(self) -> bool:
        return True

    def can(self, kind: str, fmt: str) -> bool:
        return kind in self.kinds and fmt in ENGINE_FORMATS[kind].get(self.engine, set())

    def build(self, **kwargs) -> dict[str, Path]:  # pragma: no cover - interface
        raise NotImplementedError


class Build123dTool(Tool):
    engine = "build123d"
    kinds = frozenset({"part", "assembly"})

    def build(
        self, *, kind, spec, work_dir: Path, formats, profile, inputs=None, cache_hash: str = "", source_files=None, **_
    ) -> dict[str, Path]:
        name = spec["name"]
        out = work_dir / name
        out.mkdir(parents=True, exist_ok=True)
        for file_name, path in (source_files or {}).items():  # imported models (cycax/35)
            shutil.copyfile(path, work_dir / file_name)
        if kind == "part":
            from cycax.cycad.engines.part_build123d import PartEngineBuild123d  # noqa: PLC0415

            engine = PartEngineBuild123d(name=None, path=None)
            engine.input_dir = work_dir
            shape_formats = [f for f in formats if f not in ("summary", "svg")]
            if "summary" in formats and "step" not in shape_formats:
                shape_formats.append("step")  # the summary is measured from the STEP
            files = (
                engine.export_shape(engine.make_shape(spec), out / name, shape_formats, profile)
                if shape_formats
                else []
            )
            produced = {f["type"]: f["file"] for f in files}
            if "svg" in formats:
                from cycax.report.light import sheet_svg  # noqa: PLC0415

                svg_file = out / f"{name}.svg"
                svg_file.write_text(sheet_svg(spec))
                produced["svg"] = svg_file
            if "summary" in formats:
                from cycax.summary import make_summary  # noqa: PLC0415

                summary_file = out / f"{name}.summary.json"
                summary = make_summary(spec, produced["step"], engine="build123d", cache_hash=cache_hash)
                summary_file.write_text(json.dumps(summary, indent=2))
                produced["summary"] = summary_file
            return {fmt: path for fmt, path in produced.items() if fmt in formats}
        from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d  # noqa: PLC0415

        assembly = AssemblyBuild123d(name)
        for part in spec["parts"]:
            assembly.add(part, step_file=inputs[part["hash"]]["step"])
        assembly.build(out)
        return {fmt: out / f"{name}.{fmt}" for fmt in ("step", "stl") if fmt in formats}


class FreeCADLocalTool(Tool):
    """FreeCAD on this computer (AppImage or binary), via cycax's own FreeCAD scripts."""

    engine = "freecad"
    kinds = frozenset({"part"})

    def __init__(self, app: str | None = None):
        self._app = app

    def binary(self) -> Path | None:
        if self._app and self._app != "auto":
            path = Path(self._app).expanduser()
            return path if path.exists() else None
        from cycax.cycad.engines.utils import find_appimage  # noqa: PLC0415

        found = find_appimage("FreeCAD", [Path("~/Applications")]) or shutil.which("freecad")
        if not found and platform.system() == "Windows":  # pragma: no cover - Windows only
            programs = sorted(Path("C:/Program Files").glob("FreeCAD */bin/freecad.exe"), reverse=True)
            found = programs[0] if programs else None
        return Path(found) if found else None

    def available(self) -> bool:
        return self.binary() is not None

    def build(self, *, spec, work_dir: Path, formats, **_) -> dict[str, Path]:
        app = self.binary()
        if app is None:
            msg = "FreeCAD is not installed on this computer."
            raise ToolMissingError(msg, fix="Install FreeCAD, set [tools] freecad in the user config, or use --server.")
        from cycax.cycad.engines.part_freecad_bend import is_sheet_metal_bend, run_freecad_bend  # noqa: PLC0415

        name = spec["name"]
        part_dir = work_dir / name
        part_dir.mkdir(parents=True, exist_ok=True)
        json_file = part_dir / f"{name}.json"
        json_file.write_text(json.dumps(spec))
        if is_sheet_metal_bend(spec):
            run_freecad_bend(app, json_file, work_dir)
            produced = {
                "step": part_dir / f"{name}.step",
                "fcstd": part_dir / f"{name}.FCStd",
                "dxf": part_dir / f"{name}-unfold.dxf",
            }
        else:
            from cycax.cycad.engines.engine_freecad import EngineFreeCAD  # noqa: PLC0415

            out_formats = ",".join(sorted({"stl"} | {f for f in formats if f in {"png", "dxf"}}))
            EngineFreeCAD(config={"freecad_app": str(app), "out_formats": out_formats}).build_part(json_file)
            produced = {
                "step": part_dir / f"{name}.step",
                "stl": part_dir / f"{name}.stl",
                "fcstd": part_dir / f"{name}.FCStd",
                "png": part_dir / f"{name}-all.png",
                "dxf": part_dir / f"{name}-top.dxf",
            }
        return {fmt: path for fmt, path in produced.items() if fmt in formats and path.exists()}


class OpenSCADTool(Tool):
    engine = "openscad"
    kinds = frozenset({"part"})

    def __init__(self, app: str | None = None):
        self._app = app

    def binary(self) -> Path | None:
        if self._app and self._app != "auto":
            path = Path(self._app).expanduser()
            return path if path.exists() else None
        from cycax.cycad.engines.utils import find_appimage  # noqa: PLC0415

        return find_appimage("OpenSCAD", [Path("~/Applications")]) or (
            Path(found) if (found := shutil.which("openscad")) else None
        )

    def available(self) -> bool:
        return self.binary() is not None

    def build(self, *, spec, work_dir: Path, formats, **_) -> dict[str, Path]:
        from cycax.cycad.engines.part_openscad import PartEngineOpenSCAD  # noqa: PLC0415

        name = spec["name"]
        part_dir = work_dir / name
        part_dir.mkdir(parents=True, exist_ok=True)
        json_file = part_dir / f"{name}.json"
        json_file.write_text(json.dumps(spec))
        engine = PartEngineOpenSCAD(name=name, path=work_dir, config={"stl": "stl" in formats})
        engine._json_file = json_file
        engine.build(None)
        produced = {"scad": part_dir / f"{name}.scad", "stl": part_dir / f"{name}.stl"}
        return {fmt: path for fmt, path in produced.items() if fmt in formats and path.exists()}


class ServerTool(Tool):
    """An engine on a NATS worker."""

    where = "server"

    def __init__(self, engine: str, client: ServerClient):
        self.engine = engine
        self.worker, self.kinds = SERVER_WORKERS[engine]
        self.client = client

    def available(self) -> bool:
        return self.client.available()

    def build(
        self,
        *,
        spec,
        cache_hash,
        work_dir: Path,
        formats,
        profile,
        editable=False,
        force=False,
        on_progress=None,
        source_files=None,
        inputs=None,
        **_,
    ) -> dict[str, Path]:
        return self.client.fetch(
            source_files=source_files,
            inputs=inputs,
            spec=spec,
            cache_hash=cache_hash,
            worker=self.worker,
            formats=list(formats),
            profile=profile,
            out_dir=work_dir / cache_hash,
            editable=editable,
            force=force,
            on_progress=on_progress,
        )


def local_tools(tools_settings: dict) -> dict[str, Tool]:
    return {
        "build123d": Build123dTool(),
        "freecad": FreeCADLocalTool(tools_settings.get("freecad")),
        "openscad": OpenSCADTool(tools_settings.get("openscad")),
    }


def server_tools(client: ServerClient) -> dict[str, Tool]:
    return {engine: ServerTool(engine, client) for engine in SERVER_WORKERS}


def scratch_dir() -> Path:
    return Path(tempfile.mkdtemp(prefix="cycax-build-"))
