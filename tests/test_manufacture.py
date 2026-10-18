# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Manufacturing data (task cycax/25)."""

import pytest

from cycax.cycad import Cuboid, Print3D, SheetMetal, SheetMetalBend
from cycax.manufacture import CncMill, FdmPrint, LaserCut, Manufacture
from cycax.materials import ALUMINIUM_5052_H32, PLA
from cycax.spec import spec_hash


def test_defaults_per_part_class():
    assert Print3D(part_no="a", x_size=1, y_size=1, z_size=1).export()["meta"]["manufacture"]["process"] == "3d-print"
    assert SheetMetal(part_no="a", x_size=1, y_size=1).export()["meta"]["manufacture"]["process"] == "laser-cut"
    bend = SheetMetalBend(part_no="a", x_size=10, y_size=10, z_size=1).export()["meta"]["manufacture"]
    assert [step["process"] for step in bend["steps"]] == ["laser-cut", "bend"]
    assert "manufacture" not in Cuboid(part_no="a", x_size=1, y_size=1, z_size=1).export()["meta"]


def test_human_instructions():
    clip = Print3D(
        part_no="clip",
        x_size=2,
        y_size=2,
        z_size=2,
        material=PLA,
        manufacture=FdmPrint(printer="Prusa MK4", filament="red PLA", infill=30),
    )
    (text,) = clip.export()["meta"]["manufacture"]["instructions"]
    assert text == "3D print with red PLA filament on the Prusa MK4, layer 0.2 mm, infill 30 %, no supports."
    plate = SheetMetal(part_no="p", x_size=10, y_size=10, material=ALUMINIUM_5052_H32)
    assert plate.export()["meta"]["manufacture"]["instructions"] == [
        "Laser cut from aluminium 5052-H32 sheet. Remove the burrs."
    ]
    own = Manufacture(process="waterjet", instructions="Cut on the Flow waterjet, 0.3 mm kerf.")
    assert own.human_instructions() == ["Cut on the Flow waterjet, 0.3 mm kerf."]


def test_cnc_mill_tools():
    mill = CncMill(
        machine="Shapeoko 4", stock="6 mm aluminium plate", tools=["3 mm flat end mill", "6 mm flat end mill"]
    )
    meta = mill.to_meta()
    assert meta["settings"]["tools"] == ["3 mm flat end mill", "6 mm flat end mill"]
    assert meta["instructions"] == [
        "Mill from 6 mm aluminium plate on the Shapeoko 4 with 3 mm flat end mill, then 6 mm flat end mill."
    ]


def test_manufacture_is_not_in_the_hash():
    a = Print3D(part_no="a", x_size=1, y_size=1, z_size=1)
    b = Print3D(part_no="a", x_size=1, y_size=1, z_size=1, manufacture=LaserCut(machine="Trotec"))
    assert spec_hash(a.export()) == spec_hash(b.export())


def test_bad_value():
    with pytest.raises(TypeError):
        Print3D(part_no="a", x_size=1, y_size=1, z_size=1, manufacture="print it")
