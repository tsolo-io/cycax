#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Print3D


def test_box_location():
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_sphere")

    for side in (cube.left, cube.bottom, cube.front):
        step = 2
        side.box(pos=(step, step), depth=step + 1, length=2, width=2)
    test = cube.export()

    for feature in test["features"]:
        if feature["type"] != "cut":
            continue
        if feature["side"] in ("BOTTOM", "LEFT"):
            assert feature["y"] == 7
        if feature["side"] == "BACK":
            assert feature["x"] == 7
