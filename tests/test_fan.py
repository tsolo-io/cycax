import hashlib
from pathlib import Path

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid, SheetMetal
from cycax.cycad.fan import Fan
from tests.shared import hex_code_check


def fans(tmp_path):
    face = SheetMetal(part_no="face", x_size=50, y_size=100, z_size=2)
    fan_face = Fan(width=50, depth=10, part_no="fan_face", internal=True, hole_depth=2.0, hole_diameter=3.0)

    box = Assembly("box")
    box.level(face.bottom, fan_face.top)
    box.subtract(face.bottom, fan_face)
    box.add(fan_face)
    box.add(face)

    fan_face.save(tmp_path)
    face.save(tmp_path)

    face.render("freecad")
    face.render("preview3d")


def test_fans(tmp_path):
    #This test checks that the fan is being produced as it should.

    fans(tmp_path)

    hex_code_check(tmp_path=tmp_path, filename="fan_face", ext=".json", hex_code = "213b3ecfdceaac78c23769b81f3851398089108d449e9feb09e602343dab0d24")
    

    hex_code_check(tmp_path=tmp_path, filename="face", ext=".json", hex_code = "db70922e5e252705acffa479746feda80776681ba0d1a166c2713e6ba8c491ef")
    

    hex_code_check(tmp_path=tmp_path, filename="face", ext=".scad", hex_code = "7867ac6c33eccceb5d2fdc42cf4b41aadc3a46bdf79e6834d60ca3c87d26c34e")


    hex_code_check(tmp_path=tmp_path, filename="face", ext=".stl", hex_code = "1a01f17b378a6e7c9abc54ce8680480ff5ded289bc9880f7192ac119785e0755")
    

