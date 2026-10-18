# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""The cross-engine test helpers (cycax.testing, task cycax/22)."""

import json

import pytest

from cycax import testing
from cycax.app.builder import Builder, BuildItem
from cycax.app.project import Project, Settings
from cycax.app.tools import FreeCADLocalTool
from cycax.cycad import Assembly, Print3D


def plate(hole_x: float = 10) -> Print3D:
    part = Print3D(part_no="xe_plate", x_size=40, y_size=20, z_size=5)
    part.top.hole(pos=(hole_x, 10), diameter=4.2)
    part.front.box(pos=(30, 2), width=5, length=2, depth=3)
    return part


def build(tmp_path, obj, engine: str, outputs: list[str], target: str = "t") -> dict:
    settings = Settings()
    settings.cache_folder = str(tmp_path / f"cache_{engine}")  # one cache per engine: no sharing
    settings.backend = "local"
    project = Project(tmp_path, settings)
    result = Builder(project, outputs=outputs, backend="local").build([BuildItem(f"{target}_{engine}", obj, engine)])
    built = next(iter(result.targets.values()))
    assert built.error is None, built.error
    return built.files


@pytest.fixture(scope="module")
def build123d_files(tmp_path_factory):
    return build(tmp_path_factory.mktemp("b123d"), plate(), "build123d", ["step", "stl", "glb"])


def test_formats_of_one_engine_agree(build123d_files):
    step = testing.measure(build123d_files["step"])
    assert step.exact
    assert step.solids == 1
    assert step.size == pytest.approx((40, 20, 5), abs=1e-6)
    for fmt in ("stl", "glb"):
        mesh = testing.measure(build123d_files[fmt])
        assert not mesh.exact
        assert testing.compare(step, mesh) == [], fmt


def test_glb_is_read_in_mm_and_z_up(build123d_files):
    glb = testing.measure(build123d_files["glb"])
    assert glb.bbox_max == pytest.approx((40, 20, 5), abs=1e-3)


def test_a_moved_hole_is_found(tmp_path, build123d_files):
    moved = build(tmp_path, plate(hole_x=11), "build123d", ["step", "stl"])
    exact = testing.compare(testing.measure(build123d_files["step"]), testing.measure(moved["step"]))
    assert any(problem.startswith("centre x") for problem in exact)
    mesh = testing.compare(testing.measure(build123d_files["stl"]), testing.measure(moved["stl"]))
    assert any(problem.startswith("centre x") for problem in mesh)
    with pytest.raises(AssertionError, match="centre x"):
        testing.assert_same(build123d_files["step"], moved["step"])


@pytest.mark.skipif(not FreeCADLocalTool().available(), reason="FreeCAD is not installed")
def test_build123d_and_freecad_agree(tmp_path, build123d_files):
    freecad = build(tmp_path, plate(), "freecad", ["step", "fcstd"])
    reference = testing.measure(build123d_files["step"])
    for fmt in ("step", "fcstd"):
        measured = testing.measure(freecad[fmt])
        assert measured.exact
        assert testing.compare(reference, measured) == [], fmt


def test_golden_spec(tmp_path):
    spec = plate().export()
    testing.check_golden(spec, "plate", tmp_path)  # first run writes the approved copy
    assert json.loads((tmp_path / "plate.json").read_text()) == json.loads(json.dumps(spec))
    testing.check_golden(spec, "plate", tmp_path)
    with pytest.raises(AssertionError, match="geometry changed"):
        testing.check_golden(plate(hole_x=12).export(), "plate", tmp_path)
    meta_only = json.loads(json.dumps(spec))
    meta_only["meta"]["description"] = "another text"
    with pytest.raises(AssertionError, match="only the meta changed"):
        testing.check_golden(meta_only, "plate", tmp_path)
    testing.check_golden(plate(hole_x=12).export(), "plate", tmp_path, update=True)
    testing.check_golden(plate(hole_x=12).export(), "plate", tmp_path)


def test_assembly_instances(tmp_path):
    assembly = Assembly("two_plates")
    base = Print3D(part_no="base", x_size=40, y_size=20, z_size=5)
    top = Print3D(part_no="top", x_size=40, y_size=20, z_size=3)
    assembly.add(base)
    assembly.add(top)
    top.level(bottom=base.top)
    files = build(tmp_path, assembly, "build123d", ["step"])
    instances = testing.assembly_instances(files["step"])
    assert len(instances) == 2  # noqa: PLR2004
    by_z = sorted(instances, key=lambda i: i.center[2])
    assert by_z[0].center == pytest.approx((20, 10, 2.5), abs=1e-6)
    assert by_z[1].center == pytest.approx((20, 10, 6.5), abs=1e-6)
    assert by_z[1].bbox_min[2] == pytest.approx(5, abs=1e-6)
    assert {i.name for i in instances} == {"base_1", "top_1"}  # instance names (cycax/39)
    assert all(i.hash for i in instances)  # and the part hashes
    assert by_z[1].transform[2][3] == pytest.approx(5)
