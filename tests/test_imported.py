# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Parts from imported STEP/STL files (task cycax/35)."""

import math

import build123d
import pytest

import cycax
from cycax import testing
from cycax.cycad import ImportedPart
from cycax.cycad.imported import import_object_name
from cycax.spec import spec_hash


@pytest.fixture
def vendor_step(tmp_path):
    # A 50 x 30 x 20 block with a 10 mm hole, NOT at the origin (like a vendor model).
    path = tmp_path / "psu.step"
    build123d.export_step(build123d.Pos(125, 215, 0) * (build123d.Box(50, 30, 20) - build123d.Cylinder(5, 20)), path)
    return path


def test_the_model_moves_to_the_origin(vendor_step):
    part = ImportedPart(part_no="psu", file=vendor_step)
    assert part.offset == pytest.approx((-100, -200, 10))
    assert (part.x_size, part.y_size, part.z_size) == pytest.approx((50, 30, 20))
    base = part.export()["features"][0]
    assert base["type"] == "import"
    assert base["file"] == "psu.step"
    assert len(base["sha256"]) == 64
    assert import_object_name(part.export()) == "psu-import.step"


def test_a_changed_file_changes_the_hash(vendor_step):
    first = spec_hash(ImportedPart(part_no="psu", file=vendor_step).export())
    build123d.export_step(build123d.Box(10, 10, 10), vendor_step)
    assert spec_hash(ImportedPart(part_no="psu", file=vendor_step).export()) != first


def test_build_with_a_drilled_hole(vendor_step, tmp_path):
    part = ImportedPart(part_no="psu", file=vendor_step)
    part.top.hole(pos=(5, 5), diameter=3)
    result = cycax.build(part, outputs=["step"], backend="local", project_dir=tmp_path / "proj")
    target = next(iter(result.targets.values()))
    assert target.error is None, target.error
    measured = testing.measure(target.files["step"])
    assert measured.bbox_min == pytest.approx((0, 0, 0), abs=1e-6)
    assert measured.volume == pytest.approx(50 * 30 * 20 - math.pi * 25 * 20 - math.pi * 1.5**2 * 20)


def test_no_features_on_stl(tmp_path):
    stl = tmp_path / "m.stl"
    build123d.export_stl(build123d.Box(10, 10, 10), stl)
    part = ImportedPart(part_no="m", file=stl)
    assert part.export()["features"][0]["format"] == "stl"
    part.top.hole(pos=(5, 5), diameter=2)
    with pytest.raises(ValueError, match="STEP imports only"):
        part.export()


def test_missing_or_wrong_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        ImportedPart(part_no="x", file=tmp_path / "nope.step")
    (tmp_path / "x.obj").write_text("")
    with pytest.raises(ValueError, match="STEP"):
        ImportedPart(part_no="x", file=tmp_path / "x.obj")
