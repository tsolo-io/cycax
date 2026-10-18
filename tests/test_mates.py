# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Mates solved in order: mate, align, place (task cycax/38)."""

import pytest

from cycax import testing
from cycax.app.builder import Builder, BuildItem
from cycax.app.project import Project, Settings
from cycax.cycad import Assembly, Print3D


def build_boxes(tmp_path, assembly) -> dict:
    settings = Settings()
    settings.cache_folder = str(tmp_path / "cache")
    result = Builder(Project(tmp_path, settings), outputs=["step"], backend="local").build(
        [BuildItem(assembly.name, assembly)]
    )
    target = next(iter(result.targets.values()))
    assert target.error is None, target.error
    return {i.name: (i.bbox_min, i.bbox_max) for i in testing.assembly_instances(target.files["step"])}


def tilted_on_base():
    assembly = Assembly("mated")
    base = Print3D(part_no="base", x_size=100, y_size=100, z_size=4)
    block = Print3D(part_no="block", x_size=40, y_size=20, z_size=10)
    assembly.add(base)
    assembly.add(block)
    block.move(x=30, y=40, z=50)
    block.rotate(x=30)  # tilted
    return assembly, base, block


def test_mate_puts_a_rotated_part_flat_on_another(tmp_path):
    assembly, base, block = tilted_on_base()
    assembly.mate(block.bottom, base.top)
    bottom = block.anchor("bottom")
    assert bottom.normal == pytest.approx((0, 0, -1))
    assert bottom.origin[2] == pytest.approx(4)
    assert block.z_max - block.z_min == pytest.approx(10)  # flat again: the box is 10 high
    spec = assembly.export()
    assert spec["mates"] == [
        {
            "type": "mate",
            "moving": {"instance": "block_1", "anchor": "bottom"},
            "target": {"instance": "base_1", "anchor": "top"},
            "offset": 0.0,
        }
    ]
    lo, hi = build_boxes(tmp_path, assembly)["block_1"]
    assert lo[2] == pytest.approx(4, abs=1e-6)
    assert hi[2] == pytest.approx(14, abs=1e-6)


def test_mate_with_offset():
    assembly, base, block = tilted_on_base()
    assembly.mate(block.bottom, base.top, offset=2)
    assert block.anchor("bottom").origin[2] == pytest.approx(6)


def test_align_makes_holes_coaxial():
    assembly = Assembly("aligned")
    plate = Print3D(part_no="plate", x_size=50, y_size=50, z_size=3)
    plate.top.hole(pos=(25, 25), diameter=4, name="m4")
    pin = Print3D(part_no="pin", x_size=4, y_size=4, z_size=20)
    pin.anchor("axis", pos=(2, 2, 0), normal=(0, 0, -1))
    assembly.add(plate)
    assembly.add(pin)
    pin.move(x=7, y=-3, z=10)
    pin.rotate(y=20)
    assembly.align(pin.ref("axis"), plate.ref("m4"), contact=True)
    axis = pin.anchor("axis")
    assert axis.origin == pytest.approx((25, 25, 3))
    assert abs(axis.normal[2]) == pytest.approx(1)


def test_place_frame_to_frame():
    assembly = Assembly("placed")
    rack = Print3D(part_no="rack", x_size=100, y_size=100, z_size=5)
    rack.anchor("slot", pos=(50, 50, 5), normal=(0, 0, 1), x_dir=(0, 1, 0))
    psu = Print3D(part_no="psu", x_size=30, y_size=20, z_size=10)
    psu.anchor("mount", pos=(15, 10, 0), normal=(0, 0, -1), x_dir=(1, 0, 0))
    assembly.add(rack)
    assembly.add(psu)
    psu.rotate(z=17)
    assembly.place(psu.ref("mount"), on=rack.ref("slot"))
    mount = psu.anchor("mount")
    assert mount.origin == pytest.approx((50, 50, 5))
    assert mount.x_dir == pytest.approx((0, 1, 0))
    # The psu turned 90 degrees: now 20 wide in x and 30 deep in y, centred on the slot.
    assert (psu.x_max - psu.x_min, psu.y_max - psu.y_min) == pytest.approx((20, 30))


def test_a_fixed_part_is_not_moved():
    assembly, base, block = tilted_on_base()
    assembly.mate(block.bottom, base.top)
    with pytest.raises(ValueError, match="already placed"):
        assembly.mate(base.bottom, block.top)


def test_a_later_move_breaks_the_mate():
    assembly, base, block = tilted_on_base()
    assembly.mate(block.bottom, base.top)
    block.move(z=1)
    with pytest.raises(ValueError, match="does not hold"):
        assembly.export()
