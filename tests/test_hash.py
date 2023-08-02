from pathlib import Path

from cycax.cycad import Print3D
from tests.shared import hex_code_check


def hash_cube(tmp_path: Path):

    for depth in (1,2):
        cube = Print3D(x_size=11, y_size=11, z_size=11, part_no=f"testing_hash_{depth}")
        cube.left.hole(pos=(7,7), diameter=3, depth=depth)
        cube.save(tmp_path)
        cube.render("freecad")
        cube.render("preview3d")


def test_hash(tmp_path: Path):
    # This test will check that the hash functionality is working as it should.

    hash_cube(tmp_path)
    ext=".scad"
    for depth in (1,2):
        hex_value =hex_code_check(tmp_path=tmp_path, filename="testing_hash_1", ext=ext, return_hex = True)
        hex_code_check(tmp_path=tmp_path, filename="testing_hash_2", ext=ext, hex_code=hex_value, equal = False)
        ext=".stl"
