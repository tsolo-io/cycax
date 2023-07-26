#!/usr/bin/env python3
from cycax.cycad import Print3D


def test_box_location():
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_sphere")

    for side in (cube.left, cube.bottom, cube.front):
        step = 2
        side.box(pos=(step, step), depth=step + 1, length=2, width=2)
    test = cube.export()

    for features in test["features"]:
        if features["side"] == "LEFT":
            assert features["y"] == 7

        if features["side"] == "BOTTOM":
            assert features["y"] == 7

        if features["side"] == "BACK":
            assert features["x"] == 7
