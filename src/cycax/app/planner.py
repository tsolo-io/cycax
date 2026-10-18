# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Engine selection (docs/content/engine-selection.md, task cycax/14).

Turns requested outputs of one spec into steps: which engine makes which formats, and where
(local or server).
"""

from dataclasses import dataclass, field

from cycax.app.errors import ServerUnavailableError, ToolMissingError
from cycax.app.tools import ENGINE_FORMATS, Tool

# Outputs only one engine can make (rule 1).
SINGLE_ENGINE = {"fcstd": "freecad", "dxf": "freecad", "drawing": "freecad", "scad": "openscad", "blend": "blender"}
# Fallback order when no rule picks an engine.
ENGINE_ORDER = ("build123d", "freecad", "openscad", "python", "blender")
SHEET_METAL_TYPES = frozenset(
    {"bend", "flange_hole_cut", "flat_rectangle_cut", "flat_polygon_cut", "flange_corner_round"}
)


def is_sheet_metal(spec: dict) -> bool:
    return any(feature.get("type") in SHEET_METAL_TYPES for feature in spec.get("features", []))


def choose_engine(kind: str, fmt: str, *, target_engine: str | None, sheet_metal: bool, project_engine: str) -> str:
    """The engine for one output (rules 1-4)."""
    if fmt in SINGLE_ENGINE:
        return SINGLE_ENGINE[fmt]
    can = ENGINE_FORMATS[kind]
    for engine in (target_engine, "freecad" if sheet_metal and kind == "part" else None, project_engine):
        if engine and fmt in can.get(engine, set()):
            return engine
    for engine in ENGINE_ORDER:
        if fmt in can.get(engine, set()):
            return engine
    msg = f"No engine can make {fmt} for a {kind}."
    raise ToolMissingError(msg, fix="Choose another output format.")


def default_outputs(kind: str, project_outputs: list[str], engines: dict[str, str], *, sheet_metal: bool) -> list[str]:
    """The project outputs plus the native files of the engines used (engine-selection.md, Defaults)."""
    outputs = list(dict.fromkeys(project_outputs))
    used = set(engines.values())
    if "freecad" in used and "fcstd" not in outputs:
        outputs.append("fcstd")
    if "openscad" in used and kind == "part" and "scad" not in outputs:
        outputs.append("scad")
    if sheet_metal and kind == "part" and "dxf" not in outputs:
        outputs.append("dxf")
    return outputs


@dataclass
class Step:
    engine: str
    where: str  # "local" or "server"
    tool: Tool
    formats: list[str] = field(default_factory=list)


def place(engine: str, kind: str, backend: str, local: dict[str, Tool], server: dict[str, Tool]) -> Tool:
    """Where an engine runs (rule 5)."""
    local_tool = local.get(engine)
    server_tool = server.get(engine)
    local_ok = local_tool is not None and kind in local_tool.kinds and local_tool.available()
    server_possible = server_tool is not None and kind in server_tool.kinds
    if backend == "local":
        if local_ok:
            return local_tool
        msg = f"{engine} is not available on this computer for a {kind}."
        raise ToolMissingError(msg, fix=f"Install {engine}, or build with --server or --auto.")
    if backend == "server":
        if server_possible and server_tool.available():
            return server_tool
        if not server_possible:
            msg = f"No server worker runs {engine} for a {kind}."
            raise ToolMissingError(msg, fix="Build with --local, or choose another engine.")
        msg = "The CyCAx server is not reachable."
        raise ServerUnavailableError(msg, fix="Check [server] url in cycax.toml, or build with --local.")
    if local_ok:  # auto
        return local_tool
    if server_possible and server_tool.available():
        return server_tool
    msg = f"{engine} is not on this computer and the server cannot build it."
    raise ToolMissingError(msg, fix=f"Install {engine}, or check that the CyCAx server is running.")


def plan_spec(
    spec: dict,
    *,
    outputs: list[str] | None,
    project_outputs: list[str],
    project_engine: str,
    target_engine: str | None,
    backend: str,
    local: dict[str, Tool],
    server: dict[str, Tool],
) -> list[Step]:
    """Steps for one spec: outputs grouped by the tool that makes them."""
    kind = spec["kind"]
    sheet_metal = kind == "part" and is_sheet_metal(spec)
    wanted = list(outputs) if outputs else list(project_outputs)
    engines = {
        fmt: choose_engine(
            kind, fmt, target_engine=target_engine, sheet_metal=sheet_metal, project_engine=project_engine
        )
        for fmt in wanted
    }
    if not outputs:
        wanted = default_outputs(kind, wanted, engines, sheet_metal=sheet_metal)
        for fmt in wanted:
            engines.setdefault(
                fmt,
                choose_engine(
                    kind, fmt, target_engine=target_engine, sheet_metal=sheet_metal, project_engine=project_engine
                ),
            )
    steps: dict[tuple[str, str], Step] = {}
    for fmt in wanted:
        engine = engines[fmt]
        tool = place(engine, kind, backend, local, server)
        key = (engine, tool.where)
        steps.setdefault(key, Step(engine, tool.where, tool)).formats.append(fmt)
    return list(steps.values())
