# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from itertools import combinations
from pathlib import Path

import pytest

from cycax.cycad import Print3D
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


def test_cube_add_sphere(tmp_path: Path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_add_rectangle")

    edges = combinations(("LEFT", "RIGHT", "FRONT", "BACK", "TOP", "BOTTOM"), 2)
    for edge in edges:
        if edge in (("LEFT", "RIGHT"), ("TOP", "BOTTOM"), ("FRONT", "BACK")):
            with pytest.raises(Exception):  # noqa: B017 cat the base exception in the test we have not decided on custom exceptions.
                cube.beveled_edge(edge_type="round", side1=edge[0], side2=edge[1], size=3)
        else:
            cube.beveled_edge(edge_type="round", side1=edge[0], side2=edge[1], size=3)

    for side in (cube.back, cube.left, cube.right, cube.top, cube.bottom, cube.front):
        side.box_add(pos=(3, 3), length=4, width=4, depth=7)
        side.box_add(pos=(5.5, 5.5), length=4, width=2, depth=7)
        side.cylinder(pos=(7, 7), diameter=6, height=4, original_surface=True)
        side.box_add(pos=(6.5, 6.5), length=4, width=2, depth=7, original_surface=True)
        side.sphere_add(pos=(3, 6), diameter=6, original_surface=True)
        side.hole(pos=(3, 6), diameter=2)

    # cube.save(tmp_path)
    cube.save("/home/helen/src/tsolo/test-slot")
    # cube.render("preview3d")
    cube.render("freecad")
    # cube.build(PartEngineBuild123d())
