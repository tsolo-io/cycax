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
    assert hash_value_json == "e0b35d005866ffa3ba5e26792df851ef3ce99470e363667f974d1bb9d8f410b0"

    hash_value_scad = hex_code(sphere_path=sphere_loc, filename="testing_sphere.scad")
    assert hash_value_scad == "e2e9bd90687c806b16591a6c9741f840c13edfca7cdf62d4416b562ef1df2a65"

    hash_value_freecad_stl = hex_code(sphere_path=sphere_loc, filename="testing_sphere.stl")
    assert hash_value_freecad_stl == "e6af4da27e13425a9a0b2870a69fdd25f0d2188891ab03518d72aef0b6523045"
