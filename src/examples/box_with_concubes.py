#!/usr/bin/env python3

from cycax.cycad import Assembly, Cuboid, ExternalPart, SheetMetal

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class ConCube(Cuboid):
    """This class holds the data for the corner cube."""

    def __init__(self):
        Cuboid.__init__(self, part_no="con_cube", x_size=11, y_size=11, z_size=11)
        self.calculate()

    def calculate(self):
        """Calculate the concube."""
        for side in (LEFT, BOTTOM, FRONT):
            self.make_hole(x=7, y=7, side=side, diameter=3.2, depth=2, inner=False)
            self.make_hole(x=7, y=7, side=side, diameter=2.9, depth=11, inner=True)  # Through everything
            self.make_nut(side=side, x=7, y=7, nut_type=3, depth=2, sink=1)  # Coordinates based on center of the Nut.

            # # Two holes for the bolt. The bolt go into a slightly bigger hole, then through the nut then a tight hole to act like a thread lock.

        self.make_rectangle(side=LEFT, x=7, y=10, y_size=6.2, x_size=2, z_size=3, sink=2, center=True)
        self.make_rectangle(side=BOTTOM, x=7, y=10, y_size=3, x_size=6.2, z_size=2, sink=2, center=True)
        self.make_rectangle(side=FRONT, x=7, y=10, y_size=2, x_size=6.2, z_size=3, sink=2, center=True)

        # Cut the excess material we dont want to print.
        self.make_rectangle(TOP, x=4, y=4, y_size=7, x_size=7, z_size=7)


class main:
    def main():
        box = Assembly("box")

        bottom = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="bottom")
        top = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="bottom")
        left = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
        right = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
        front = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")
        back = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")

        # HD = ExternalPart(part_no="SSD_SATA_2.5")

        box.rotateFreezeFront(left)
        box.rotateFreezeFront(right)
        box.rotateFreezeLeft(front)
        box.rotateFreezeLeft(back)

        box.level(front, BACK, bottom, FRONT)
        box.level(back, FRONT, bottom, BACK)

        box.level(left, RIGHT, bottom, LEFT)
        box.level(right, LEFT, bottom, RIGHT)

        box.level(top, TOP, back, TOP)

        box.level(left, FRONT, front, FRONT)
        box.level(right, FRONT, front, FRONT)

        cubes = [0, 0, 0, 0, 0, 0, 0, 0]
        for cube in range(8):
            cubes[cube] = ConCube()

        count = 0
        increment = 2
        while count != 8:
            box.rotateFreezeTop(cubes[count])
            count = count + 1
            if count == 7:
                count = increment
                increment = increment + 2

        for cube in range(1, 8, 2):
            box.rotateFreezeLeft(cubes[cube])
            box.rotateFreezeLeft(cubes[cube])
            box.rotateFreezeTop(cubes[cube])

        for cube in range(4):
            box.level(cubes[cube], RIGHT, right, LEFT)

        for cube in range(4, 8):
            box.level(cubes[cube], LEFT, left, RIGHT)

        for cube in range(2, 6):
            box.level(cubes[cube], BACK, back, FRONT)

        for cube in [0, 1, 6, 7]:
            box.level(cubes[cube], FRONT, front, BACK)

        for cube in range(0, 8, 2):
            box.level(cubes[cube], BOTTOM, bottom, TOP)

        for cube in range(1, 8, 2):
            box.level(cubes[cube], TOP, top, BOTTOM)

        for cube in range(0, 8, 2):
            box.subtract(bottom, TOP, cubes[cube])

        for cube in range(4, 8):
            box.subtract(left, RIGHT, cubes[cube])

        for cube in [0, 1, 6, 7]:
            box.subtract(front, BACK, cubes[cube])

        # HD.make_hole(20, 20, TOP, 20, 20)

        # box.rotateFreezeFront(HD)
        # box.level(HD, LEFT, right, RIGHT)

        box.add(bottom)
        box.add(left)
        box.add(right)
        box.add(front)
        box.add(back)
        box.add(top)
        # box.add(HD)

        for cube in range(8):
            box.add(cubes[cube])

        box.render()

    if __name__ == "__main__":
        main()
