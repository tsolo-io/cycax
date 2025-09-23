# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad import Print3D
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


def test_cube_add_sphere(tmp_path: Path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_add_sphere")

    for side in (cube.back, cube.left, cube.right, cube.top, cube.bottom, cube.front):
        side.sphere_add(pos=(7.0, 7.0), diameter=6)
        side.sphere_add(pos=(5.5, 5.5), diameter=6)
        side.sphere_add(pos=(7, 7), diameter=6)
        side.sphere_add(pos=(6.5, 6.5), diameter=6)
        side.sphere_add(pos=(9, 9), diameter=6)
        side.hole(pos=(9, 9), diameter=2)

    cube.save(tmp_path)
    cube.render("preview3d")
    cube.build(PartEngineBuild123d())
