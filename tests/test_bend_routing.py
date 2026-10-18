# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# The CLI must send sheet-metal parts to the FreeCAD bend engine, not the generic one.
from cycax.cycad import SheetMetal, SheetMetalBend
from cycax.cycad.engines.part_freecad_bend import is_sheet_metal_bend


def test_part_with_bends_needs_the_bend_engine():
    bracket = SheetMetalBend(part_no="bracket", x_size=80, y_size=50, z_size=3)
    bracket.front.bend(angle=90, height=20)
    assert is_sheet_metal_bend(bracket.export())


def test_plain_part_uses_the_generic_engine():
    plate = SheetMetal(part_no="plate", x_size=80, y_size=50, z_size=3)
    plate.top.hole(pos=(10, 10), diameter=4)
    assert not is_sheet_metal_bend(plate.export())
