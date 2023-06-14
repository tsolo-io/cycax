#!/usr/bin/env python3

from ConCube import ConCube

from cycax.cycad.assembly import Assembly
from cycax.cycad.external_part import ExternalPart
from cycax.cycad.sheet_metal import SheetMetal

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


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
