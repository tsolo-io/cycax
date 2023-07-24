import hashlib
from pathlib import Path

from cycax.cycad import Print3D


def sphere_cube(sphere_path):
    cube = Print3D(x_size=11, y_size=11, z_size=11, part_no="testing_sphere")

    for side in (cube.left, cube.right, cube.top, cube.bottom, cube.front, cube.back):
        side.sphere(pos=[7, 7], diameter=6, sink=1)

    sphere_path.mkdir()

    cube.save(sphere_path)
    cube.render("freecad")
    cube.render("preview3d")


def hex_code(sphere_path, filename: str):
    """Test save on assembly and parts."""

    filename = sphere_path / "testing_sphere" / filename

    content = filename.read_text()
    hash_value_file = hashlib.sha256(content.encode("UTF-8")).hexdigest()

    return hash_value_file


def test_sphere(tmp_path):
    sphere_loc = tmp_path / "sphere"

    sphere_cube(sphere_loc)

    hash_value_json = hex_code(sphere_path=sphere_loc, filename="testing_sphere.json")
    assert hash_value_json == "858423461f59456c8bbea67cb0903243bf03561e90f377e73c86ecb20fe56b00"

    hash_value_scad = hex_code(sphere_path=sphere_loc, filename="testing_sphere.scad")
    assert hash_value_scad == "31952d1282ed60f4e767a861f9aa03cf47a109cc1a67dd96916e0017367f7ecc"

    hash_value_freecad_stl = hex_code(sphere_path=sphere_loc, filename="testing_sphere.stl")
    assert hash_value_freecad_stl == "e426ee7d533aea2eaaf200cde2928f03944d5125c2475676289bc2e8c737bb35"
