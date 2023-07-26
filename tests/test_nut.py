#!/usr/bin/env python3
import hashlib
from pathlib import Path

from cycax.cycad import Print3D


def nutty_cube(nut_path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_nut")

    for side in (cube.left, cube.right, cube.top, cube.bottom, cube.front, cube.back):
        side.nut(pos=[7, 7], nut_type="M3", depth=2)  # Coordinates based on center of the Nut.

    nut_path.mkdir()

    cube.save(nut_path)
    cube.render("freecad")
    cube.render("preview3d")


def hex_code(nut_path, filename: str):
    """Test save on assembly and parts."""

    filename = nut_path / "testing_nut" / filename

    content = filename.read_text()
    hash_value_file = hashlib.sha256(content.encode("UTF-8")).hexdigest()

    return hash_value_file


def test_nut(tmp_path):
    nut_loc = tmp_path / "nut"

    nutty_cube(nut_loc)

    hash_value_json = hex_code(nut_path=nut_loc, filename="testing_nut.json")
    assert hash_value_json == "22144e25a8dc044b89e4f5795ace224f90a87ae087647de05edb674daab09d93"

    hash_value_scad = hex_code(nut_path=nut_loc, filename="testing_nut.scad")
    assert hash_value_scad == "a2d137c720a5f204749757c5e6a2eacd003244c8642d55b85efd36db7e165815"

    hash_value_freecad_stl = hex_code(nut_path=nut_loc, filename="testing_nut.stl")
    assert hash_value_freecad_stl == "fdf00b4b0a62fbb105624bda0a7e3c870010f367515d7f7c6397c677a12fae86"
