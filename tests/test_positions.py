# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from cycax.cycad import Assembly, SheetMetal
from cycax.parts.fan import Fan


def _assembly_with_part():
    assembly = Assembly("t")
    part = SheetMetal(part_no="p", x_size=10, y_size=20, z_size=2)
    assembly.add(part)
    part.move(x=100, y=50, z=5)
    return assembly, part


def test_part_center_uses_absolute_bounds():
    _, part = _assembly_with_part()
    assert tuple(part.center) == (105.0, 60.0, 6.0)


def test_assembly_center_is_the_bounding_box_center():
    assembly, part = _assembly_with_part()
    other = SheetMetal(part_no="q", x_size=10, y_size=20, z_size=2)
    assembly.add(other)  # at the origin
    assert tuple(assembly.center) == (55.0, 35.0, 3.5)


def test_assembly_at_center_moves_the_center():
    assembly, _ = _assembly_with_part()
    assembly.at(center_x=0, center_y=0, center_z=0)
    assert tuple(assembly.center) == (0.0, 0.0, 0.0)


def test_assembly_at_accepts_zero():
    assembly, part = _assembly_with_part()
    assembly.at(min_x=0)
    assert part.position[0] == 0
    with pytest.raises(ValueError, match="both min_x and center_x"):
        assembly.at(min_x=0, center_x=0)


def test_fan_features_are_not_duplicated():
    fan = Fan(size=80, thickness=10, part_no="fan80")
    first = [f.export() for f in fan.features]
    assert len(first) == len({repr(f) for f in first})  # no repeated feature
