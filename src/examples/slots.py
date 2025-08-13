#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid, Print3D, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP


class Cube(Cuboid):
    def __init__(self, side: str, *, horizontal: bool = True):
        self.side_name = side.lower()
        self.hrz = horizontal
        super().__init__(part_no=f"cube-{self.side_name}", x_size=100, y_size=100, z_size=100)
        self.calculate()

    def calculate(self):
        diameter = 6
        side = getattr(self, self.side_name)
        side.slot(
            pos=(diameter, self.y_size / 2), width=diameter, length=self.x_size - 2 * diameter
        )
        side.slot(
            pos=(diameter, self.y_size / 2),
            width=diameter,
            length=self.x_size - 2 * diameter,
            external_subtract=True,
        )
        side.hole(pos=(self.x_size / 2, self.y_size / 2), diameter=diameter * 2, depth=5)  # Marker, should point down


def main():
    name = "slots"
    assembly = Assembly(name)
    base_board = SheetMetal(part_no="base", x_size=1300, y_size=700, z_size=15)
    assembly.add(base_board)
    top_cube = None
    left_on = base_board.left
    for side in SIDES:
        rotation_str = {LEFT: "yyy", RIGHT: "y", FRONT: "yx", BACK: "xzyy", TOP: "zyy", BOTTOM: "z"}[side]
        for horizontal in (True, False):
            for subtract in (True, False):
                cube = Cube(side, horizontal=horizontal)
                assembly.add(cube, f"cube-{side}-{horizontal}-{subtract}")
                if subtract:
                    cube.rotate(rotation_str)
                if horizontal and subtract:
                    cube.level(bottom=base_board.top, back=base_board.back, left=left_on)
                    cube.move(x=100)
                    left_on = cube.right
                else:
                    cube.level(bottom=base_board.top, back=top_cube.front, left=top_cube.left)
                    cube.move(y=-100)
                top_cube = cube
                if subtract:
                    cube.level(bottom=base_board.top, subtract=True)


    assembly.save(f"./build/{name}")
    # assembly.render()
    assembly.build(engine=AssemblyBuild123d(name), part_engines=[PartEngineBuild123d()])


if __name__ == "__main__":
    main()
