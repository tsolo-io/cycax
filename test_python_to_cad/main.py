import json
from cuboid import cuboid
from con_cube import con_cube
from decode import decode
from assembly import assembly
from sheet_metal import sheet_metal

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class main:
    def main():
        box = assembly("box")

        bottom = sheet_metal(x_size=100, y_size=100, z_size=2, part_no="bottom")
        top = sheet_metal(x_size=100, y_size=100, z_size=2, part_no="bottom")
        left = sheet_metal(x_size=100, y_size=104, z_size=2, part_no="side")
        right = sheet_metal(x_size=100, y_size=104, z_size=2, part_no="side")
        front = sheet_metal(x_size=100, y_size=100, z_size=2, part_no="front")
        back = sheet_metal(x_size=100, y_size=100, z_size=2, part_no="front")

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
            cubes[cube] = con_cube()

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

        box.add(bottom, make_file=True)
        box.add(left, make_file=True)
        box.add(right)
        box.add(front, make_file=True)
        box.add(back)
        box.add(top)

        for cube in range(8):
            box.add(cubes[cube], True)

        box.render()

    if __name__ == "__main__":
        main()
