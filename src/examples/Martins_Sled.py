#!/usr/bin/env python3

from cycax.cycad import Assembly, Cuboid, SheetMetal, Print3D


class MiniItxMb(Print3D):
    def __init__(self):
        super().__init__(
            part_no="mini-itx-motherboard", x_size=170.18, y_size=170.18, z_size=60
        )
        self.colour = "blue"
        # There is a 2mm overhang at the back and left for the connector plate, if that is builtin.

    def definition(self):
        # Connectors are the back of the MB.
        # PCIe slot is on the left.
        yb = self.y_size - 10.16
        yf = yb - 157.94
        yo = yb - 22.86
        x1 = 6.35
        x2 = x1 + 157.48

        # TODO: The MB holes are a little "off", looks wrong. Need to render in FreeCAD so I can check beter. Probably my measurements.
        for pos in ((x1, yf), (x1, yb), (x2, yf), (x2, yo)):
            self.bottom.hole(pos=pos, diameter=3.2, inner=False)
            self.top.hole(pos=pos, diameter=4)

        stand_off_size = 10
        self.bottom.box(
            # FIXME: It seems length is on the Y and width on the X. They should be swapped.
            pos=(-1, yf + 4),
            width=self.x_size + 2,
            length=120,
            depth=stand_off_size,
        )
        self.bottom.box(
            # FIXME: It seems length is on the Y and width on the X. They should be swapped.
            pos=(0, yf + 4),
            width=self.x_size - 20,
            length=150,
            depth=stand_off_size,
        )
        self.bottom.box(
            # FIXME: It seems length is on the Y and width on the X. They should be swapped.
            pos=(20, -4),
            width=self.x_size - 40,
            length=250,
            depth=stand_off_size,
        )


class ConnCube(Print3D):
    """This class holds the data for the corner cube."""

    def __init__(self):
        super().__init__(part_no="conn-cube", x_size=11, y_size=11, z_size=11)

    def definition(self):
        """Calculate the concube."""
        for side in (self.left, self.bottom, self.front):
            side.hole(pos=[7, 7], diameter=3.2, depth=2, inner=False)
            side.hole(pos=[7, 7], diameter=2.9, inner=True)  # Through everything
            side.nut(
                pos=[7, 7], nut_type="M3", depth=2, sink=1
            )  # Coordinates based on center of the Nut.
            side.box(
                pos=[7, 10], depth=2, width=6.2, length=3, sink=2, center=True
            )  # Holes to fit the nuts into

        # Cut the excess material we dont want to print.
        self.top.box(pos=[4, 4], length=7, width=7, depth=7)


THICKNESS = 1  # Thickness of sheetmetal
LENGTH = 750
HEIGHT = 44.5 * 5 - 3
INNER_WIDTH = 82  # TODO: Lookup width of PSU
WIDTH = INNER_WIDTH + 2 * THICKNESS


def main():
    box = Assembly("2UH12L1N")

    front = SheetMetal(
        x_size=WIDTH, y_size=HEIGHT, z_size=THICKNESS, part_no="face-plate"
    )
    top = SheetMetal(
        x_size=LENGTH, y_size=INNER_WIDTH, z_size=THICKNESS, part_no="top-plate"
    )
    left = SheetMetal(
        x_size=LENGTH, y_size=HEIGHT, z_size=THICKNESS, part_no="left-plate"
    )
    right = SheetMetal(
        x_size=LENGTH, y_size=HEIGHT, z_size=THICKNESS, part_no="right-plate"
    )
    right.colour = "green"
    motherboard = MiniItxMb()
    motherboard.save()
    motherboard.render("OpenSCAD")


    box.rotateFreezeFront(motherboard)
    box.rotateFreezeTop(top)
    box.rotateFreezeTop(left)
    box.rotateFreezeFront(left)
    box.rotateFreezeTop(right)
    box.rotateFreezeFront(right)
    box.rotateFreezeLeft(front)

    box.level(left.front, front.back)
    box.level(right.right, front.right)
    box.level(left.top, front.top)
    box.level(right.top, front.top)
    box.level(left.right, front.left)
    box.level(right.left, front.right)
    box.level(top.front, front.back)
    box.level(top.top, front.top)
    box.level(top.left, left.right)
    box.level(motherboard.back, left.back)
    box.level(motherboard.left, left.right)

    cubes = []

    for cube in cubes:
        box.add(cube)
        
    box.add(left)
    box.add(right)
    box.add(front)
    box.add(top)
    box.add(motherboard)

    box.save()
    box.render()


if __name__ == "__main__":
    main()
