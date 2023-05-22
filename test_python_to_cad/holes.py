from location import location


class holes(location):
    """This class will store data on holes."""

    def __init__(
        self, side: str, x: float, y: float, z: float, big: float, depth: float
    ):
        """This method createsa hole."""
        location.__init__(self, x, y, z, side)
        self.diameter = big
        self.depth = depth

    def export(self):
        """This will create a dictionary of the hole."""
        dict_hole = {
            "name": "hole",
            "type": "cut",
            "side": self.side,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "diameter": self.diameter,
            "depth": self.depth,
        }
        return dict_hole
