from pathlib import Path

from cycax.cycad import Print3D
from tests.shared import hex_code_check


def nutty_cube(tmp_path: Path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_nut")

    for side in (cube.left, cube.right, cube.top, cube.bottom, cube.front, cube.back):
        side.nut(pos=(7.0, 7.0), nut_type="M3", depth=2)  # Coordinates based on center of the Nut.

    cube.save(tmp_path)
    cube.render("freecad")
    cube.render("preview3d")


def test_nut(tmp_path: Path):
    # This test will check that the nut is still being produced as it should.

    nutty_cube(tmp_path)

    # TODO: Reinstate this test but compare the contents not the hash.
    # hex_code_check(
    #     tmp_path=tmp_path,
    #     filename="testing_nut",
    #     ext=".json",
    #     hex_code="22144e25a8dc044b89e4f5795ace224f90a87ae087647de05edb674daab09d93",
    # )

    # TODO: Reinstate this test but compare the contents not the hash.
    # hex_code_check(
    #     tmp_path=tmp_path,
    #     filename="testing_nut",
    #     ext=".scad",
    #     hex_code="a2d137c720a5f204749757c5e6a2eacd003244c8642d55b85efd36db7e165815",
    # )

    hex_code_check(
        tmp_path=tmp_path,
        filename="testing_nut",
        ext=".stl",
        hex_codes=(
            "fdf00b4b0a62fbb105624bda0a7e3c870010f367515d7f7c6397c677a12fae86",
            "6fc6198e2798017a6c0480fe539b4bad0760c3e932c16c9aa96a6d240c7ba917",
        ),
    )
