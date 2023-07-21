from cycax.cycad import Assembly, Print3D

# Test that the entire system works together

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class ConCube(Print3D):
    """This class holds the data for the corner cube."""

    def __init__(self):
        super().__init__(part_no="con_cube", x_size=11, y_size=11, z_size=11)

    def definition(self):
        """Calculate the concube."""
        side = self.left
        side.hole(pos=[7, 7], diameter=3.2, depth=2, external_subtract=True)
        side.hole(pos=[7, 7], diameter=3.2, depth=2)
        side.hole(pos=[7, 7], diameter=2.9)  # Through everything
        side.nut(pos=[7, 7], nut_type="M3", depth=2, sink=1)  # Coordinates based on center of the Nut.
        side.box(pos=[7, 10], depth=2, length=6.2, width=3, sink=2, center=True)  # holes to fit the nuts into
        side.slot(pos=[2, 3], width=4, length=4, depth=4, external_subtract=True)


def test_dynamic():
    box = Assembly("box")
    cube = ConCube()
    box.add(cube)
    test_cube = cube.export()
    test_box = box.export()

    assert "name" in test_cube
    assert "features" in test_cube
    for item in test_cube["features"]:
        assert "name" in item
        assert "type" in item
        assert "side" in item

        assert "x" in item
        assert "y" in item
        assert "z" in item

    assert "name" in test_box
    assert "parts" in test_box
