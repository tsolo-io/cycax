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

    box.level(front_side.back, bottom_side.front)
    box.level(back_side.front, bottom_side.back)

    box.level(left_side.right, bottom_side.left)
    box.level(right_side.left, bottom_side.right)
    box.level(right_side_fancy.left, bottom_side.right)

    box.level(top_side.top, back_side.top)
    box.level(top_side_fancy.top, back_side.top)

    box.level(left_side.front, front_side.front)
    box.level(right_side.front, front_side.front)
    box.level(right_side_fancy.front, front_side.front)

    cc = ConCube(name="ConCube")
    box.add(cc)
    cc.assembly = box
    box.level(cc.top, top_side.bottom)
    box.level(cc.back, top_side.back)
    box.level(cc.right, right_side.left)
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

    for part in box_dict["parts"]:
        if part["part_no"] == "concube":
            move_comp = part["position"]
        if part["part_no"] == "concube_fancy":
            move_fancy_comp = part["position"]

    assert move_comp == move_fancy_comp, "The two level methods do not result in the same output."

    top_side_dict = top_side.export()
    top_side_fancy_dict = top_side_fancy.export()

    right_side_dict = right_side.export()
    right_side_fancy_dict = right_side_fancy.export()

    assert top_side_dict == top_side_fancy_dict, "Subtract on level does not result in the same output."

    assert right_side_dict == right_side_fancy_dict, "Subtract on level does not result in the same output."
