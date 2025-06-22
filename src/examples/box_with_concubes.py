#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Assembly, Print3D, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


class ConnCube(Print3D):
    """This class holds the data for the corner cube."""

    def __init__(self):
        super().__init__(part_no="con_cube", x_size=11, y_size=11, z_size=11)

    def definition(self):
        """Calculate the concube."""
        for side in (self.left, self.bottom, self.front):
            side.hole(pos=(7, 7), diameter=3.2, depth=2)
            side.hole(pos=(7, 7), diameter=2.9)  # Through everything
            side.hole(pos=(7, 7), diameter=3.2, external_subtract=True)  # Through everything
            side.nut(pos=(7, 7), nut_type="M3", depth=2, sink=1)  # Coordinates based on center of the Nut.
            side.box(pos=(7, 10), depth=2, width=6.2, length=3, sink=2, center=True)  # holes to fit the nuts into

        # Cut the excess material we dont want to print.
        self.top.box(pos=(4, 4), length=7, width=7, depth=7)


def main():
    box = Assembly("box")

    bottom = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="bottom")
    top = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="bottom")
    left = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
    right = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
    front = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")
    back = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")

    box.rotate_freeze_front(left)
    box.rotate_freeze_front(right)
    box.rotate_freeze_left(front)
    box.rotate_freeze_left(back)

    box.level(front.back, bottom.front)
    box.level(back.front, bottom.back)

    box.level(left.right, bottom.left)
    box.level(right.left, bottom.right)

    box.level(top.top, back.top)

    box.level(left.front, front.front)
    box.level(right.front, front.front)

    cubes = [ConnCube() for cube in range(8)]

    count = 0
    increment = 2
    while count != 8:  # noqa: PLR2004
        box.rotate_freeze_top(cubes[count])
        count = count + 1
        if count == 7:  # noqa: PLR2004
            count = increment
            increment = increment + 2

    for cube in range(1, 8, 2):
        box.rotate_freeze_left(cubes[cube])
        box.rotate_freeze_left(cubes[cube])
        box.rotate_freeze_top(cubes[cube])

    for cube in range(4):
        box.level(cubes[cube].right, right.left)

    for cube in range(4, 8):
        box.level(cubes[cube].left, left.right)

    for cube in range(2, 6):
        box.level(cubes[cube].back, back.front)

    for cube in [0, 1, 6, 7]:
        box.level(cubes[cube].front, front.back)

    for cube in range(0, 8, 2):
        box.level(cubes[cube].bottom, bottom.top)

    for cube in range(1, 8, 2):
        box.level(cubes[cube].top, top.bottom)

    for cube in range(0, 8, 2):
        box.subtract(bottom.top, cubes[cube])

    for cube in range(4, 8):
        box.subtract(left.right, cubes[cube])

    for cube in [0, 1, 6, 7]:
        box.subtract(front.back, cubes[cube])

    box.add(bottom)
    box.add(left)
    box.add(right)
    box.add(front)
    box.add(back)
    # box.add(top)

    for cube in range(8):
        box.add(cubes[cube])

    box.save("./build/box_with_concubes")
    box.build(engine=AssemblyBuild123d(box.name), part_engines=[PartEngineBuild123d()])


if __name__ == "__main__":
    main()
