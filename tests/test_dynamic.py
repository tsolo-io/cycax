# SPDX-FileCopyrightText: 2025 Tsolo.io
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

    cubes = [0, 0, 0, 0, 0, 0, 0, 0]
    for cube in range(8):
        cubes[cube] = ConCube()

    start = 0
    for _count in range(8):
        for cube in range(start, 8):
            box.rotate_freeze_top(cubes[cube])
        start = start + 2

    for cube in range(1, 8, 2):
        box.rotate_freeze_front(cubes[cube])
        box.rotate_freeze_front(cubes[cube])
        box.rotate_freeze_top(cubes[cube])

    for cube in range(0, 8, 2):
        box.level(cubes[cube].bottom, bottom.top)

    for cube in range(1, 8, 2):
        box.level(cubes[cube].top, top.bottom)

    for cube in [0, 1, 2, 7]:
        box.level(cubes[cube].right, right.left)

    for cube in [3, 4, 5, 6]:
        box.level(cubes[cube].left, left.right)

    for cube in [2, 4, 5, 7]:
        box.level(cubes[cube].back, back.front)

    for cube in [0, 1, 6, 3]:
        box.level(cubes[cube].front, front.back)

    for cube in range(0, 8, 2):
        box.subtract(bottom.top, cubes[cube])

    for cube in [3, 5, 6, 4]:
        box.subtract(left.right, cubes[cube])

    for cube in [2, 7, 4, 5]:
        box.subtract(back.front, cubes[cube])

    box.merge(top, bottom)
    box.merge(front, back)
    box.merge(left, right)

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
            {"part_no": "top", "position": [0, 0, 0], "rotate": [], "rotmax": [100, 100, 2], "colour": "gray"},
            {
                "part_no": "side",
                "position": [-2, -2, 0],
                "rotate": [{"axis": "y", "angle": 90}],
                "rotmax": [100, 104, 2],
                "colour": "gray",
            },
            {
                "part_no": "side",
                "position": [100, -2, 0],
                "rotate": [{"axis": "y", "angle": 90}],
                "rotmax": [100, 104, 2],
                "colour": "gray",
            },
            {
                "part_no": "front",
                "position": [0, -2, 0],
                "rotate": [{"axis": "x", "angle": 90}],
                "rotmax": [100, 100, 2],
                "colour": "gray",
            },
            {
                "part_no": "front",
                "position": [0, 100, 0],
                "rotate": [{"axis": "x", "angle": 90}],
                "rotmax": [100, 100, 2],
                "colour": "gray",
            },
            {"part_no": "top", "position": [0, 0, 98], "rotate": [], "rotmax": [100, 100, 2], "colour": "gray"},
            {
                "part_no": "con_cube",
                "position": [89, 0, 2],
                "rotate": [{"axis": "z", "angle": 90}],
                "rotmax": [11, 11, 11],
                "colour": "red",
            },
            {
                "part_no": "con_cube",
                "position": [89, 0, 87],
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "rotmax": [11, 11, 11],
                "colour": "red",
            },
            {
                "part_no": "con_cube",
                "position": [89, 89, 2],
                "rotate": [{"axis": "z", "angle": 90}, {"axis": "z", "angle": 90}],
                "rotmax": [11, 11, 11],
                "colour": "red",
            },
            {
                "part_no": "con_cube",
                "position": [0, 0, 87],
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "rotmax": [11, 11, 11],
                "colour": "red",
            },
            {
                "part_no": "con_cube",
                "position": [0, 89, 2],
                "rotate": [{"axis": "z", "angle": 90}, {"axis": "z", "angle": 90}, {"axis": "z", "angle": 90}],
                "rotmax": [11, 11, 11],
                "colour": "red",
            },
            {
                "part_no": "con_cube",
                "position": [0, 89, 87],
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "rotmax": [11, 11, 11],
                "colour": "red",
            },
            {
                "part_no": "con_cube",
                "position": [0, 0, 2],
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "rotmax": [11, 11, 11],
                "colour": "red",
            },
            {
                "part_no": "con_cube",
                "position": [89, 89, 87],
                "rotate": [
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "z", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "y", "angle": 90},
                    {"axis": "z", "angle": 90},
                ],
                "rotmax": [11, 11, 11],
                "colour": "red",
            },
        ],
    }
