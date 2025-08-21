# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Assembly, Print3D

# Tests the merging of a part.


def test_merge():
    length = 1000
    width = 100
    thickness = 2

    assembly = Assembly("assembly-test")
    mypart1 = Print3D(x_size=length, y_size=width, z_size=thickness, part_no="part-test1")
    mypart2 = Print3D(x_size=length, y_size=width, z_size=thickness, part_no="part-test2")

    mypart1.top.hole(pos=[7, 7], diameter=3.2, depth=2, external_subtract=True)
    mypart1.top.hole(pos=[7, 7], diameter=3.2, depth=2)
    mypart2.top.hole(pos=[7, 7], diameter=3.2, depth=2, external_subtract=True)
    mypart2.top.hole(pos=[7, 7], diameter=3.2, depth=2)

    mypart1.top.nut(pos=[5, 5], nut_type="M3", depth=2)
    mypart1.left.hole(pos=[7, 7], diameter=3.2, depth=2, external_subtract=True)
    mypart1.left.hole(pos=[7, 7], diameter=3.2, depth=2)

    mypart2.left.hole(pos=[4, 3], diameter=3.2, depth=2, external_subtract=True)
    mypart2.left.hole(pos=[4, 3], diameter=3.2, depth=2)

    assembly.add(mypart1)
    assembly.add(mypart2)
    mypart1.merge(mypart2)

    assert mypart1.features == mypart2.features
    assert mypart2.external_features == mypart1.external_features
