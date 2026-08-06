# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Assembly, Print3D, SheetMetal

# Test that the entire system works together

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class ConCube(Print3D):
    """This class holds the data for the corner cube."""

    def __init__(self):
        super().__init__(part_no="con_cube", x_size=11, y_size=11, z_size=11)

    def definition(self):
        """Calculate the concube."""
        for side in (self.left, self.bottom, self.front):
            side.hole(pos=[7, 7], diameter=3.2, depth=2, external_subtract=False)
            side.hole(pos=[7, 7], diameter=3.2, depth=2)
            side.hole(pos=[7, 7], diameter=2.9)  # Through everything
            side.nut(pos=[7, 7], nut_type="M3", depth=2, sink=1)  # Coordinates based on center of the Nut.
            side.box(pos=[7, 10], depth=2, length=6.2, width=3, sink=2, center=True)  # holes to fit the nuts into

        # Cut the excess material we dont want to print.
        self.top.box(pos=[4, 4], length=7, width=7, depth=7)


def test_dynamic():
    box = Assembly("box")

    bottom = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="top")
    top = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="top")
    left = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
    right = SheetMetal(x_size=100, y_size=104, z_size=2, part_no="side")
    front = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")
    back = SheetMetal(x_size=100, y_size=100, z_size=2, part_no="front")

    left.rotate_freeze_front()
    right.rotate_freeze_front()
    front.rotate_freeze_left()
    back.rotate_freeze_left()

    front.back.level(bottom.front)
    back.front.level(bottom.back)

    left.right.level(bottom.left)
    right.left.level(bottom.right)

    top.top.level(back.top)

    left.front.level(front.front)
    right.front.level(front.front)

    cubes = [0, 0, 0, 0, 0, 0, 0, 0]
    for cube in range(8):
        cubes[cube] = ConCube()

    start = 0
    for _count in range(8):
        for cube in range(start, 8):
            cubes[cube].rotate_freeze_top()
        start = start + 2

    for cube in range(1, 8, 2):
        cubes[cube].rotate_freeze_front()
        cubes[cube].rotate_freeze_front()
        cubes[cube].rotate_freeze_top()

    for cube in range(0, 8, 2):
        cubes[cube].bottom.level(bottom.top)

    for cube in range(1, 8, 2):
        cubes[cube].top.level(top.bottom)

    for cube in [0, 1, 2, 7]:
        cubes[cube].right.level(right.left)

    for cube in [3, 4, 5, 6]:
        cubes[cube].left.level(left.right)

    for cube in [2, 4, 5, 7]:
        cubes[cube].back.level(back.front)

    for cube in [0, 1, 6, 3]:
        cubes[cube].front.level(front.back)

    for cube in range(0, 8, 2):
        bottom.top.subtract(cubes[cube])

    for cube in [3, 5, 6, 4]:
        left.right.subtract(cubes[cube])

    for cube in [2, 7, 4, 5]:
        back.front.subtract(cubes[cube])

    top.merge(bottom)
    front.merge(back)
    left.merge(right)

    box.add(bottom)
    box.add(left)
    box.add(right)
    box.add(front)
    box.add(back)
    box.add(top)

    for cube in range(8):
        box.add(cubes[cube])

    assert box.export() == {
        "name": "box",
        "parts": [
            {
                "name": "top",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "rotate": [],
                "x_size": 100,
                "y_size": 100,
                "z_size": 2,
                "colour": [0.5, 0.5, 0.5],
                "hash": "",
            },
            {
                "name": "side",
                "x": -2.0,
                "y": -2.0,
                "z": 0.0,
                "rotate": [{"axis": "y", "angle": 90}],
                "x_size": 100,
                "y_size": 104,
                "z_size": 2,
                "colour": [0.5, 0.5, 0.5],
                "hash": "",
            },
            {
                "name": "side",
                "x": 100.0,
                "y": -2.0,
                "z": 0.0,
                "rotate": [{"axis": "y", "angle": 90}],
                "x_size": 100,
                "y_size": 104,
                "z_size": 2,
                "colour": [0.5, 0.5, 0.5],
                "hash": "",
            },
            {
                "name": "front",
                "x": 0.0,
                "y": -2.0,
                "z": 0.0,
                "rotate": [{"axis": "x", "angle": 90}],
                "x_size": 100,
                "y_size": 100,
                "z_size": 2,
                "colour": [0.5, 0.5, 0.5],
                "hash": "",
            },
            {
                "name": "front",
                "x": 0.0,
                "y": 100.0,
                "z": 0.0,
                "rotate": [{"axis": "x", "angle": 90}],
                "x_size": 100,
                "y_size": 100,
                "z_size": 2,
                "colour": [0.5, 0.5, 0.5],
                "hash": "",
            },
            {
                "name": "top",
                "x": 0.0,
                "y": 0.0,
                "z": 98.0,
                "rotate": [],
                "x_size": 100,
                "y_size": 100,
                "z_size": 2,
                "colour": [0.5, 0.5, 0.5],
                "hash": "",
            },
            {
                "name": "con_cube",
                "x": 89.0,
                "y": 0.0,
                "z": 2.0,
                "rotate": [{"axis": "z", "angle": 90}],
                "x_size": 11,
                "y_size": 11,
                "z_size": 11,
                "colour": [1.0, 0.0, 0.0],
                "hash": "",
            },
            {
                "name": "con_cube",
                "x": 89.0,
                "y": 0.0,
                "z": 87.0,
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "x_size": 11,
                "y_size": 11,
                "z_size": 11,
                "colour": [1.0, 0.0, 0.0],
                "hash": "",
            },
            {
                "name": "con_cube",
                "x": 89.0,
                "y": 89.0,
                "z": 2.0,
                "rotate": [{"axis": "z", "angle": 90}, {"axis": "z", "angle": 90}],
                "x_size": 11,
                "y_size": 11,
                "z_size": 11,
                "colour": [1.0, 0.0, 0.0],
                "hash": "",
            },
            {
                "name": "con_cube",
                "x": 0.0,
                "y": 0.0,
                "z": 87.0,
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "x_size": 11,
                "y_size": 11,
                "z_size": 11,
                "colour": [1.0, 0.0, 0.0],
                "hash": "",
            },
            {
                "name": "con_cube",
                "x": 0.0,
                "y": 89.0,
                "z": 2.0,
                "rotate": [{"axis": "z", "angle": 90}, {"axis": "z", "angle": 90}, {"axis": "z", "angle": 90}],
                "x_size": 11,
                "y_size": 11,
                "z_size": 11,
                "colour": [1.0, 0.0, 0.0],
                "hash": "",
            },
            {
                "name": "con_cube",
                "x": 0.0,
                "y": 89.0,
                "z": 87.0,
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "x_size": 11,
                "y_size": 11,
                "z_size": 11,
                "colour": [1.0, 0.0, 0.0],
                "hash": "",
            },
            {
                "name": "con_cube",
                "x": 0.0,
                "y": 0.0,
                "z": 2.0,
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "x_size": 11,
                "y_size": 11,
                "z_size": 11,
                "colour": [1.0, 0.0, 0.0],
                "hash": "",
            },
            {
                "name": "con_cube",
                "x": 89.0,
                "y": 89.0,
                "z": 87.0,
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "x_size": 11,
                "y_size": 11,
                "z_size": 11,
                "colour": [1.0, 0.0, 0.0],
                "hash": "",
            },
        ],
    }
