# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad import Print3D
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


def test_cube_add_cylinder(tmp_path: Path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_add_cylinder")

    for side in (cube.back, cube.left, cube.right, cube.top, cube.bottom, cube.front):
        side.cylinder(pos=(5.5, 5.5), diameter=6, height=4)
        side.cylinder(pos=(7, 7), diameter=6, height=4, sink=4)
        side.cylinder(pos=(6.5, 6.5), diameter=6, height=6)
        side.cylinder(pos=(9, 9), diameter=6, height=8)
        side.hole(pos=(9, 9), diameter=2)

    # cube.save(tmp_path)
    cube.save("/home/helen/src/tsolo/test-slot")
    cube.render("preview3d")
    cube.build(PartEngineBuild123d())
