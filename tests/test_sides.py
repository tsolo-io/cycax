# Tests for functionality on part sides.

from pathlib import Path
from cycax.cycad import Print3D
from tests.shared import hex_code_check
from cycax.cycad import SheetMetal
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP


def test_sides():
    for side in (LEFT, RIGHT, TOP, BOTTOM, FRONT, BACK):
        assert side in SIDES


def test_opposite():
    """Test that the opposite function of sides work."""

    mypart = SheetMetal(x_size=20, y_size=20, z_size=20, part_no="chunk-of-iron")
    for side_name in SIDES:
        side = getattr(mypart, side_name.lower())
        opposite = side.opposite
        assert side == opposite.opposite, "The opposite of the opposite should be the starting point."

    assert mypart.right.opposite == mypart.left
    assert mypart.top.opposite == mypart.bottom
    assert mypart.front.opposite == mypart.back

def complex_box(tmp_path: Path):
    cube = Print3D(x_size=20, y_size=20, z_size=20, part_no="testing_side")
    
    views=[]
    for side in (cube.left, cube.right, cube.top, cube.bottom, cube.front, cube.back):
        side.hole(pos=[3, 13], diameter=2, depth=2)
        side.nut(pos=[14, 9], nut_type="m6iso", depth=2)
        side.box(pos=[4, 5], width=3,length=5, depth=2)
        views.append(("SVG", side.name))
    cube.save(tmp_path)
    cube.render("freecad", engine_config = {"out_formats": views})
    cube.render("preview3d")


def test_side(tmp_path: Path):
    # This test will check that the nut is still being produced as it should.

    complex_box(tmp_path)

    hex_value =hex_code_check(tmp_path=tmp_path, filename="testing_side", ext="-top.svg", return_hex = True)
    
    for side in ("bottom", "left", "right", "front", "back"):
        hex_code_check(
            tmp_path=tmp_path,
            filename="testing_side",
            ext=f"-{side}.svg",
            hex_code=hex_value,
        )
