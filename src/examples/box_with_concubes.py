#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Assembly, Print3D, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


class CornerCube(Print3D):
    """This class holds the data for the corner cube."""

    def __init__(self, assembly):
        super().__init__(part_no="corner_cube", x_size=15, y_size=15, z_size=15, assembly=assembly)

    def definition(self):
        """Calculate the corner cube."""
        for side, pos in ((self.left, (5, 10)), (self.bottom, (10, 5)), (self.front, (10, 10))):
            side.hole(pos=pos, diameter=3.2, depth=2)
            side.hole(pos=pos, diameter=2.9, depth=10)  # Through everything
            side.hole(pos=pos, diameter=3.2, external_subtract=True)  # Through everything


def main():
    box = Assembly("box")

    bottom = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="bottom")
    left = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
    right = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
    front = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")
    back = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")

    box.add(bottom)
    box.add(left)
    box.add(right)
    box.add(front)
    box.add(back)
    left.rotate_freeze_front()
    right.rotate_freeze_front()
    front.rotate_freeze_left()
    back.rotate_freeze_left()

    box.level(front.back, bottom.front)
    box.level(back.front, bottom.back)
    box.level(left.right, bottom.left)
    box.level(right.left, bottom.right)
    box.level(left.front, front.front)
    box.level(right.front, front.front)

    # Bottom Cubes
    cc = CornerCube(assembly=box)
    cc.level(bottom=bottom.top, front=front.back, left=left.right, subtract=True)
    cc = CornerCube(assembly=box)
    cc.rotate("z")
    cc.level(bottom=bottom.top, front=front.back, right=right.left, subtract=True)
    cc = CornerCube(assembly=box)
    cc.rotate("zzz")
    cc.level(bottom=bottom.top, back=back.front, left=left.right, subtract=True)
    cc = CornerCube(assembly=box)
    cc.rotate("zz")
    cc.level(bottom=bottom.top, back=back.front, right=right.left, subtract=True)

    # Top Cubes
    cc = CornerCube(assembly=box)
    cc.rotate("xxz")
    cc.level(top=front.top)
    cc.level(front=front.back, left=left.right, subtract=True)
    cc = CornerCube(assembly=box)
    cc.rotate("xxzz")
    cc.level(top=front.top)
    cc.level(front=front.back, right=right.left, subtract=True)
    cc = CornerCube(assembly=box)
    cc.rotate("xx")
    cc.level(top=front.top)
    cc.level(back=back.front, left=left.right, subtract=True)
    cc = CornerCube(assembly=box)
    cc.rotate("xxzzz")
    cc.level(top=front.top)
    cc.level(back=back.front, right=right.left, subtract=True)

    box.save("./build/box_with_concubes")
    box.build(engine=AssemblyBuild123d(box.name), part_engines=[PartEngineBuild123d()])


if __name__ == "__main__":
    main()
