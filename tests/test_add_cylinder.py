# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from numpy import sinc

from cycax.cycad import Print3D
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD


def test_cube_add_cylinder(tmp_path: Path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_add_cylinder")

    cube.bottom.cylinder(pos=(3, 5), diameter=3, height=8)
    cube.bottom.cylinder(pos=(8, 5), diameter=3, height=8, sink=8)

    # for side in (cube.back, cube.left, cube.right, cube.top, cube.bottom, cube.front):
    #     side.cylinder(pos=(5.5, 5.5), diameter=6, height=4)
    #     side.cylinder(pos=(7, 7), diameter=6, height=4)
    #     side.cylinder(pos=(9, 9), diameter=6, height=8)
    #     side.hole(pos=(6, 6), diameter=2, depth=15)

    cube.save("/home/helen/src/tsolo/test-slot")
    # cube.render("freecad")
    cube.render("preview3d")
    cube.build(PartEngineBuild123d())
    cube.render("freecad")
