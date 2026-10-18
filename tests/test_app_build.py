# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# The service layer: engine selection, local builds with build123d, the local cache.
import pytest

import cycax
from cycax.app import planner
from cycax.app.builder import Builder, BuildItem
from cycax.app.errors import ServerUnavailableError, ToolMissingError
from cycax.app.events import TargetDone
from cycax.app.project import Project, Settings
from cycax.app.tools import Build123dTool
from cycax.cycad import SheetMetal, SheetMetalBend
from cycax.spec import spec_hash


class _Unreachable:
    def available(self):
        return False


def _project(tmp_path, **settings):
    return Project(tmp_path, Settings(cache_folder=str(tmp_path / "cache"), backend="local", **settings))


def test_choose_engine_rules():
    choose = planner.choose_engine
    assert choose("part", "fcstd", target_engine=None, sheet_metal=False, project_engine="build123d") == "freecad"
    assert choose("part", "step", target_engine=None, sheet_metal=False, project_engine="build123d") == "build123d"
    assert choose("part", "step", target_engine="freecad", sheet_metal=False, project_engine="build123d") == "freecad"
    assert choose("part", "step", target_engine=None, sheet_metal=True, project_engine="build123d") == "freecad"
    assert choose("part", "scad", target_engine=None, sheet_metal=False, project_engine="build123d") == "openscad"
    assert choose("assembly", "blend", target_engine=None, sheet_metal=False, project_engine="build123d") == "blender"


def test_default_outputs_add_native_files():
    assert planner.default_outputs("part", ["step"], {"step": "freecad"}, sheet_metal=True) == ["step", "fcstd", "dxf"]
    assert planner.default_outputs("part", ["step"], {"step": "build123d"}, sheet_metal=False) == ["step"]


def test_place_follows_the_backend():
    local = {"build123d": Build123dTool()}
    server = {"freecad": type("S", (), {"kinds": {"part"}, "available": lambda self: False, "where": "server"})()}
    assert planner.place("build123d", "part", "auto", local, server) is local["build123d"]
    with pytest.raises(ToolMissingError):
        planner.place("freecad", "part", "local", local, server)
    with pytest.raises(ServerUnavailableError):
        planner.place("freecad", "part", "server", local, server)
    with pytest.raises(ToolMissingError, match="not on this computer"):
        planner.place("freecad", "part", "auto", local, server)


def test_build_a_part_locally_then_from_cache(tmp_path):
    project = _project(tmp_path)
    plate = SheetMetal(part_no="plate", x_size=60, y_size=40, z_size=2)
    plate.top.hole(pos=(30, 20), diameter=5)
    events = []
    result = cycax.build(plate, outputs=["step", "stl"], project=project, on_event=events.append)
    assert result.ok, result.targets
    files = result.files
    assert sorted(files) == ["step", "stl"]
    assert files["step"] == tmp_path / "build" / "plate" / "plate.step"
    assert files["step"].stat().st_size > 0
    done = [e for e in events if isinstance(e, TargetDone)]
    assert done[0].cached is False
    # Second build: everything comes from the local cache.
    again = cycax.build(plate, outputs=["step", "stl"], project=project)
    assert again.targets["plate"].cached is True
    cache_files = sorted(p.name for p in (tmp_path / "cache").rglob("*") if p.is_file())
    assert "plate-build123d-standard.step" in cache_files
    assert "manifest.json" in cache_files


def test_profile_changes_the_stl(tmp_path):
    project = _project(tmp_path)
    from cycax.cycad import Cylinder

    def roller():
        return Cylinder(part_no="roller", diameter=40, height=10)

    draft = cycax.build(roller(), outputs=["stl"], profile="draft", project=project).files["stl"].stat().st_size
    fine = cycax.build(roller(), outputs=["stl"], profile="fine", project=project).files["stl"].stat().st_size
    assert fine > draft


def test_sheet_metal_without_freecad_fails_clearly(tmp_path, monkeypatch):
    project = _project(tmp_path, tools={"freecad": str(tmp_path / "no-freecad")})
    bracket = SheetMetalBend(part_no="bracket", x_size=80, y_size=50, z_size=3)
    bracket.front.bend(angle=90, height=20)
    result = cycax.build(bracket, project=project)  # backend local, FreeCAD missing
    target = result.targets["bracket"]
    assert not result.ok
    assert "freecad" in target.error.lower()
    assert target.fix


def test_build_an_assembly_locally(tmp_path):
    project = _project(tmp_path)
    assembly = cycax.Assembly("pair")
    small = SheetMetal(part_no="plate", x_size=10, y_size=10, z_size=2)
    big = SheetMetal(part_no="plate", x_size=40, y_size=10, z_size=2)
    assembly.add(small)
    assembly.add(big)
    big.move(y=20)
    result = cycax.build(assembly, outputs=["step"], project=project)
    assert result.ok, result.targets
    import build123d

    shape = build123d.import_step(str(result.files["step"]))
    assert len(shape.solids()) == 2  # noqa: PLR2004
    assert shape.volume == pytest.approx(10 * 10 * 2 + 40 * 10 * 2, rel=1e-6)


class _FakeBlender:
    """A Blender worker on the server that records what it is given."""

    engine, where, kinds = "blender", "server", frozenset({"part", "assembly"})

    def __init__(self):
        self.calls = []

    def available(self):
        return True

    def build(self, *, formats, work_dir, inputs=None, spec, **_):
        self.calls.append({"formats": formats, "inputs": inputs})
        work_dir.mkdir(parents=True, exist_ok=True)
        png = work_dir / f"{spec['name']}-blender-standard.png"
        png.write_bytes(b"\x89PNG fake")
        return {"png": png}


def test_a_blender_part_render_gets_the_part_stl_first(tmp_path):
    """Blender renders a part from its STL (blender/09): the builder makes the STL (here
    build123d, locally) and hands it over as an input, like an assembly's parts."""
    project = Project(tmp_path, Settings(cache_folder=str(tmp_path / "cache"), backend="auto"))
    plate = SheetMetal(part_no="plate", x_size=30, y_size=20, z_size=2)
    builder = Builder(project, outputs=["png"])
    blender = _FakeBlender()
    builder.server["blender"] = blender
    result = builder.build([BuildItem(target="plate", obj=plate, engine="blender")])
    assert result.ok, {name: target.error for name, target in result.targets.items()}
    (call,) = blender.calls
    assert call["formats"] == ["png"]
    ((part_hash, files),) = call["inputs"].items()
    assert part_hash == spec_hash(plate.export())
    assert files["stl"].exists()
