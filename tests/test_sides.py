# Tests for functionality on part sides.

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
