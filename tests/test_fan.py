#!/usr/bin/env python3
import hashlib
from pathlib import Path

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid, SheetMetal
from cycax.cycad.fan import Fan


def fans(fan_path):
    face = SheetMetal(part_no="face", x_size=50, y_size=100, z_size=2)
    fan_face = Fan(width=50, depth=10, part_no="fan_face", internal=True, hole_depth=2.0, hole_diameter=3.0)

    box = Assembly("box")
    box.level(face.bottom, fan_face.top)
    box.subtract(face.bottom, fan_face)
    box.add(fan_face)
    box.add(face)

    fan_path.mkdir()

    fan_face.save(fan_path)
    face.save(fan_path)

    # face.render("simple2D")
    # the plotter creates warnings
    face.render("freecad")
    face.render("preview3d")


def hex_code(fan_path, filename: str, ext: str):
    """Test save on assembly and parts."""

    filename = fan_path / filename / f"{filename}{ext}"

    content = filename.read_text()
    hash_value_file = hashlib.sha256(content.encode("UTF-8")).hexdigest()

    return hash_value_file


def test_fans(tmp_path):
    fan_loc = tmp_path / "fan"

    fans(fan_loc)

    hash_value_fan_face_json = hex_code(fan_path=fan_loc, filename="fan_face", ext=".json")
    assert hash_value_fan_face_json == "f35f4e190dddca585ba682fe51b59d67593a872006dc1acdf846fe5656162600"

    hash_value_face_json = hex_code(fan_path=fan_loc, filename="face", ext=".json")
    assert hash_value_face_json == "9831e01b4a94f87d758873c3bdcab28fc9d0a6035ca3861b0bdd99943660acb4"

    hash_value_face_scad = hex_code(fan_path=fan_loc, filename="face", ext=".scad")
    assert hash_value_face_scad == "ab7e3b361b402855028548790e4246de753c4f7d011222cb05aeec400534d828"

    hash_value_face_stl = hex_code(fan_path=fan_loc, filename="face", ext=".stl")
    assert hash_value_face_stl == "1a01f17b378a6e7c9abc54ce8680480ff5ded289bc9880f7192ac119785e0755"

    # hash_value_face_s2d = hex_code(fan_path = fan_loc, filename = "face", ext = "-s2d.svg")
    # assert hash_value_face_s2d == "f760ada689c45c34f39cf344983e63fed0184def206d1c0050fa95e674b2acff"
    # the plot does not have a constant hash value
