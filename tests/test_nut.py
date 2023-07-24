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
    assert hash_value_json == "f00f5009ca121dfa2db41bdd6592b67b0b20c1c4ced4625320b90254c2ee6c78"

    hash_value_scad = hex_code(nut_path=nut_loc, filename="testing_nut.scad")
    assert hash_value_scad == "7aae373b878863a76495f135759c735beb2068964c0d03769ed4d1ce282317d5"

    hash_value_freecad_stl = hex_code(nut_path=nut_loc, filename="testing_nut.stl")
    assert hash_value_freecad_stl == "3b9a4beaa11870172d0de40d343d7e048091ff84ee5a2ab125a5bf2a132d8aab"
