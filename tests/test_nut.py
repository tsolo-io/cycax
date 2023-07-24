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
    assert hash_value_json == "62758173fcc8bb82f24858c064dcd38a4e503ef9fa2258a3e009b7cd194dbb2b"

    hash_value_scad = hex_code(nut_path=nut_loc, filename="testing_nut.scad")
    assert hash_value_scad == "14db7e009a8d78b0a1a1427fb7d64727b39f092ea5714adf81d03bf37c70d478"

    hash_value_freecad_stl = hex_code(nut_path=nut_loc, filename="testing_nut.stl")
    assert hash_value_freecad_stl == "cbca5fcead7645ca95d076949df4b0b9f769d3f9c070b70eb2b5e036a936cc5b"
