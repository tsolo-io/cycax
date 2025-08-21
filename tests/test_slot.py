# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from itertools import product

from pathlib import Path
from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid, Print3D, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP

from .shared import json_compare_models, stl_compare_models


class Cube(Cuboid):
    def __init__(self, side: str, *, horizontal: bool = True):
        self.side_name = side.lower()
        self.hrz = horizontal
        if horizontal:
            self.part_no = f"cube-{self.side_name}-horizontal"
        else:
            self.part_no = f"cube-{self.side_name}-vertical"
        name = self.part_no
        super().__init__(part_no=name, x_size=100, y_size=100, z_size=100)
        self.calculate()
        if self.hrz:
            self.colour = "blue"

    def calculate(self):
        diameter = 6
        side = getattr(self, self.side_name)
        if self.hrz:
            pos = (diameter, self.y_size / 2)
        else:
            pos = (self.x_size / 2, diameter)
        side.slot(pos=pos, width=diameter, length=self.x_size - 2 * diameter, horizontal=self.hrz)
        side.slot(
            pos=pos, width=diameter, length=self.x_size - 2 * diameter, external_subtract=True, horizontal=self.hrz
        )
        side.hole(pos=(self.x_size / 2, self.y_size / 2), diameter=diameter * 2, depth=5)  # Marker, should point down


def assemble(side: str, *, horizontal: bool) -> Assembly:
    """Make an assembly with a small cube on a base plate.

    The cube has a slot and the slot is subtracted from the base plate.
    The cube is rotated so that all the base plates are the same,
    regardless of the side or if its a horizontal or vertical slot.

    Args:
        side: The side of the cube.
        horizontal: Whether the cube is horizontal or vertical.

    Returns:
        Assembly: The assembled cube on a base plate.
    """
    alignment = "h" if horizontal else "v"
    name = f"slots-{side}-{alignment}"
    assembly = Assembly(name.lower())
    base_board = SheetMetal(part_no="base", x_size=300, y_size=300, z_size=15)
    assembly.add(base_board)
    rotation_str = {LEFT: "yyy", RIGHT: "y", FRONT: "yx", BACK: "xzyy", TOP: "zyy", BOTTOM: "z"}[side]
    cube = Cube(side=side, horizontal=horizontal)
    assembly.add(cube)
    cube.rotate(rotation_str)
    if not horizontal:
        cube.rotate("z")
    cube.level(bottom=base_board.top, front=base_board.front, left=base_board.left)
    cube.move(x=100, y=100)
    cube.level(bottom=base_board.top, subtract=True)
    return assembly


def test_slots(tmp_path):
    """Test slots.

    A cube with a slot is created for every side and orientation.
    This cube is rotated so the slot is at the bottom, then the cube is subtracted from a base plate.

    The cube is created in Build123d and in FreeCAD the output STL files are compared.
    The JSON of the base plates are compared to ensure they are identical.
    """
    base_plate = None
    base_plate_special = None
    for side, horizontal in product(SIDES, (True, False)):
        assembly = assemble(side, horizontal=horizontal)
        assembly.save(tmp_path / assembly.name)
        if horizontal:
            pname = f"cube_{side.lower()}_horizontal"
        else:
            pname = f"cube_{side.lower()}_vertical"
        stl = tmp_path / assembly.name / pname / f"{pname}.stl"
        build123d_stl = stl.with_name(f"{pname}_build123d.stl")
        assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d()])
        stl.rename(build123d_stl)
        #####
        assembly.build(part_engines=[PartEngineFreeCAD()])
        #####
        # Check that the STL files produced by FreeCAD and Build123d are the same.
        #####
        stl_compare_models(build123d_stl, stl)
        #####
        # Test that each baseplate is correct by checking that it is the same as the previous one.
        my_base_plate = tmp_path / assembly.name / "base" / "base.json"


        #As these holes are inserted from the far side there actual y value is y_value = y-width - provided_y_value 
        if assembly.name in ("slots_back_h", "slots_back_v", "slots_left_v", "slots_left_h"): 
            if base_plate_special:
                #####
                json_compare_models(my_base_plate, base_plate_special)
                #####
            base_plate_special = my_base_plate

        else:
            if base_plate:
                #####
                json_compare_models(my_base_plate, base_plate)
                #####
            base_plate = my_base_plate