#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Assembly, Print3D, SheetMetal

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class ConCube(Print3D):
    """This class holds the data for the corner cube."""

    def __init__(self, name: str):
        super().__init__(part_no=name, x_size=11, y_size=11, z_size=11)

    def definition(self):
        """Calculate the concube."""
        for side in (self.left, self.bottom, self.front):
            side.hole(pos=[7, 7], diameter=3.2, depth=2)
            side.hole(pos=[7, 7], diameter=3.2, depth=2, external_subtract=True)
            side.hole(pos=[7, 7], diameter=2.9)  # Through everything
            side.nut(pos=[7, 7], nut_type="M3", depth=2, sink=1)  # Coordinates based on center of the Nut.
            side.box(pos=[7, 10], depth=2, width=6.2, length=3, sink=2, center=True)  # holes to fit the nuts into

        # Cut the excess material we dont want to print.
        self.top.box(pos=[4, 4], length=7, width=7, depth=7)


def test_level_new():
    box = Assembly("box")

    top_side = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="top")
    box.add(top_side)
    right_side = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="right")
    box.add(right_side)

    top_side_fancy = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="top")
    box.add(top_side_fancy)
    right_side_fancy = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="right")
    box.add(right_side_fancy)

    bottom_side = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="top")
    box.add(bottom_side)

    left_side = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
    box.add(left_side)
    front_side = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")
    box.add(front_side)
    back_side = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")
    box.add(back_side)

    left_side.rotate_freeze_front()

    right_side.rotate_freeze_front()
    right_side_fancy.rotate_freeze_front()

    front_side.rotate_freeze_left()
    back_side.rotate_freeze_left()


    front_side.back.level(bottom_side.front)
    back_side.front.level(bottom_side.back)

    left_side.right.level(bottom_side.left)
    right_side.left.level(bottom_side.right)
    right_side_fancy.left.level(bottom_side.right)

    top_side.top.level(back_side.top)
    top_side_fancy.top.level(back_side.top)

    left_side.front.level(front_side.front)
    right_side.front.level(front_side.front)
    right_side_fancy.front.level(front_side.front)

    cc = ConCube(name="ConCube")
    box.add(cc)
    cc.assembly = box
    cc.back.level(top_side.back)
    cc.top.level(top_side.bottom)
    cc.right.level(right_side.left)
    top_side.bottom.subtract(cc)
    right_side.left.subtract(cc)

    cc_fancy = ConCube(name="ConCube_Fancy")
    box.add(cc_fancy)
    cc_fancy.assembly = box
    top_side.assembly = box
    right_side.assembly = box
    cc_fancy.level(back=top_side.back)
    cc_fancy.level(top=top_side.bottom, right=right_side.left, subtract=True)

    box_dict = box.export()

    top_side_dict = top_side.export()
    top_side_fancy_dict = top_side_fancy.export()

    right_side_dict = right_side.export()
    right_side_fancy_dict = right_side_fancy.export()

    assert top_side_dict == top_side_fancy_dict, "Subtract on level does not result in the same output."

    assert right_side_dict == right_side_fancy_dict, "Subtract on level does not result in the same output."

    for part in box_dict["parts"]:
        if part["part_no"] == "concube":
            move_comp = part["position"]
        if part["part_no"] == "concube_fancy":
            move_fancy_comp = part["position"]

    assert move_comp == move_fancy_comp, "The two level methods do not result in the same output."
