# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Placement transform, rotate() in degrees and turn() (task cycax/32)."""

import math

import pytest

from cycax import testing
from cycax.app.builder import Builder, BuildItem
from cycax.app.project import Project, Settings
from cycax.cycad import Assembly, Print3D, placement


def project(tmp_path) -> Project:
    settings = Settings()
    settings.cache_folder = str(tmp_path / "cache")
    settings.backend = "local"
    return Project(tmp_path, settings)


def dsl_box(part):
    return (part.x_min, part.y_min, part.z_min), (part.x_max, part.y_max, part.z_max)


def built_boxes(tmp_path, assembly) -> dict[str, tuple]:
    result = Builder(project(tmp_path), outputs=["step"]).build([BuildItem(assembly.name, assembly)])
    target = next(iter(result.targets.values()))
    assert target.error is None, target.error
    return {i.name: (i.bbox_min, i.bbox_max) for i in testing.assembly_instances(target.files["step"])}


def test_rotation_matrices():
    m = placement.rotation("z", 90)
    assert placement.apply(m, (1, 0, 0)) == (0.0, 1.0, 0.0)  # counter-clockwise
    assert placement.is_quarter_turns(m)
    assert not placement.is_quarter_turns(placement.rotation("x", 30))


def test_rotate_takes_degrees_and_turn_takes_letters():
    part = Print3D(part_no="p", x_size=40, y_size=20, z_size=5)
    with pytest.raises(TypeError, match='use turn\\("xz"\\)'):
        part.rotate("xz")
    with pytest.raises(TypeError):
        part.rotate(w=10)
    with pytest.raises(ValueError, match="turn"):
        part.turn("q")


def test_rotate_30_about_the_centre():
    part = Print3D(part_no="p", x_size=40, y_size=20, z_size=5)
    part.rotate(z=30)
    lo, hi = dsl_box(part)
    c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
    width, depth = 40 * c + 20 * s, 40 * s + 20 * c
    assert hi[0] - lo[0] == pytest.approx(width)
    assert hi[1] - lo[1] == pytest.approx(depth)
    assert ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2) == pytest.approx((20, 10))  # the centre stays
    assert part.rotation == [{"axis": "z", "angle": 30.0}]


def test_turn_keeps_the_old_bounds():
    part = Print3D(part_no="p", x_size=40, y_size=20, z_size=5)
    part.turn("xz")
    assert dsl_box(part) == ((0, 0, 0), (5, 40, 20))


@pytest.mark.parametrize("how", ["rotate30", "turn", "rotate_then_level"])
def test_the_engine_puts_the_part_where_the_dsl_says(tmp_path, how):
    assembly = Assembly(f"a_{how}")
    base = Print3D(part_no="base", x_size=100, y_size=100, z_size=4)
    plate = Print3D(part_no="plate", x_size=40, y_size=20, z_size=5)
    plate.top.hole(pos=(10, 10), diameter=4)
    assembly.add(base)
    assembly.add(plate)
    if how == "rotate30":
        plate.move(x=30, y=40)
        plate.rotate(z=30)
    elif how == "turn":
        plate.turn("xz")
        plate.move(x=10, y=20)
    else:
        plate.rotate(x=30, z=45)
        plate.level(bottom=base.top)
    boxes = built_boxes(tmp_path, assembly)
    lo, hi = boxes["plate_1"]  # instance names (cycax/39)
    want_lo, want_hi = dsl_box(plate)
    assert lo == pytest.approx(want_lo, abs=1e-3)
    assert hi == pytest.approx(want_hi, abs=1e-3)


def test_assembly_rotate_about_its_centre(tmp_path):
    assembly = Assembly("turned")
    a = Print3D(part_no="a", x_size=20, y_size=10, z_size=10)
    b = Print3D(part_no="b", x_size=20, y_size=10, z_size=10)
    assembly.add(a)
    assembly.add(b)
    b.level(left=a.right)
    assembly.rotate(z=90)
    boxes = built_boxes(tmp_path, assembly)
    for part in (a, b):
        lo, hi = boxes[f"{part.part_no}_1"]
        assert lo == pytest.approx(dsl_box(part)[0], abs=1e-3)
        assert hi == pytest.approx(dsl_box(part)[1], abs=1e-3)
    # The pair (40 x 10) about its centre (20, 5): now 10 wide and 40 deep around the same centre.
    assert min(a.x_min, b.x_min) == pytest.approx(15)
    assert max(a.y_max, b.y_max) == pytest.approx(25)


def test_subtract_with_an_angle_is_not_supported_yet():
    assembly = Assembly("s")
    a = Print3D(part_no="a", x_size=20, y_size=10, z_size=10)
    a.top.hole(pos=(5, 5), diameter=2, external_subtract=True)
    a.rotate(z=30)
    with pytest.raises(NotImplementedError):
        list(a._final_place())


def test_read_back_matches_the_spec_placements(tmp_path):
    """cycax/39: every instance of the build123d STEP has its instance name, part hash and
    exactly the spec transform."""
    assembly = Assembly("readback")
    base = Print3D(part_no="base", x_size=100, y_size=100, z_size=4)
    a = Print3D(part_no="plate", x_size=40, y_size=20, z_size=5)
    b = Print3D(part_no="plate", x_size=40, y_size=20, z_size=5)
    assembly.add(base)
    assembly.add(a)
    assembly.add(b)
    a.rotate(z=30)
    a.level(bottom=base.top)
    b.turn("x")
    b.move(x=50, y=50)
    spec = assembly.export()
    result = Builder(project(tmp_path), outputs=["step"]).build([BuildItem("readback", assembly)])
    target = next(iter(result.targets.values()))
    assert target.error is None, target.error
    read = {i.name: i for i in testing.assembly_instances(target.files["step"])}
    assert set(read) == {p["instance"] for p in spec["parts"]}
    for entry in spec["parts"]:
        instance = read[entry["instance"]]
        assert instance.hash == entry["hash"]
        for row_read, row_spec in zip(instance.transform, entry["transform"], strict=True):
            assert row_read == pytest.approx(row_spec, abs=1e-6)
