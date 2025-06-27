# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad import Print3D
from tests.shared import stl_compare


def sphere_cube(tmp_path: Path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_sphere")

    for side in (cube.left, cube.right, cube.top, cube.bottom, cube.front, cube.back):
        side.sphere(pos=(7.0, 7.0), diameter=6, sink=1)

    cube.save(tmp_path)
    cube.render("freecad")
    cube.render("preview3d")


def test_sphere(tmp_path: Path):
    sphere_cube(tmp_path)

    # TODO: Reinstate this test but compare the contents not the hash.
    # hex_code_check(
    #     tmp_path=tmp_path,
    #     filename="testing_sphere",
    #     ext=".json",
    #     hex_code="e0b35d005866ffa3ba5e26792df851ef3ce99470e363667f974d1bb9d8f410b0",
    # )

    # TODO: Reinstate this test but compare the contents not the hash.
    # hex_code_check(
    #    tmp_path=tmp_path,
    #    filename="testing_sphere",
    #    ext=".scad",
    #    hex_code="e2e9bd90687c806b16591a6c9741f840c13edfca7cdf62d4416b562ef1df2a65",
    # )
    assert stl_compare(tmp_path / "testing_sphere" / "testing_sphere.stl", Path("tests/references/sphere.stl"))
