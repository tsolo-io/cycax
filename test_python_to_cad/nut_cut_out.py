from location import location


class nut_cut_out(location):
    """Class for holding the data for nuts."""

    nuts = {
        "type": 3,
        "Diameter": 6.01,
        "Height": 2.4,
        "type": 6,
        "Diameter": 11.05,
        "Height": 5.2,
    }

    def __init__(
        self, side: str, x: float, y: float, z: float, type: float, depth: float
    ):
        """THis method will create a nut."""
        location.__init__(self, x, y, z, side)
        self.type = type
        self.depth = depth

    def export(self):
        """This method will create a dictionary of the nut."""
        dict_nut = {
            "name": "nut",
            "type": "cut",
            "side": self.side,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "diameter": self.type,
            "depth": self.depth,
        }
        return dict_nut