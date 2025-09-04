# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad import Print3D
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


def test_cube_add_sphere(tmp_path: Path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_add_rectangle")

    for side in (cube.back, cube.left, cube.right, cube.top, cube.bottom, cube.front):
        side.box_add(pos=(3, 3), length=4, width=4, depth=7)
        side.box_add(pos=(5.5, 5.5), length=4, width=2, depth=7)
        side.box_add(pos=(7, 7), length=4, width=2, depth=7)
        side.box_add(pos=(6.5, 6.5), length=4, width=2, depth=7)
        side.sphere_add(pos=(9, 9), diameter=6, sink=20)
        side.hole(pos=(9, 9), diameter=2)

    # cube.save(tmp_path)
    cube.save("/home/helen/src/tsolo/test-slot")
    cube.render("preview3d")
    # cube.render("freecad")
    cube.build(PartEngineBuild123d())
