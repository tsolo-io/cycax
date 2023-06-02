from cycax.cycad.location import Location


class Holes(Location):
    """This class will store data on holes."""

    def __init__(self, side: str, x: float, y: float, z: float, big: float, depth: float):
        """This method createsa hole."""
        Location.__init__(self, x, y, z, side)
        self.diameter = big
        self.depth = depth

    def export(self):
        """This will create a dictionary of the hole."""
        dict_hole = {
            "name": "hole",
            "type": "cut",
            "side": self.side,
            "x": str(self.x),
            "y": str(self.y),
            "z": str(self.z),
            "diameter": self.diameter,
            "depth": str(self.depth),
        }
        return dict_hole


class RectangleCutOut(Location):
    """This class can be used for cutting a hole that is not square but rather of the definied parameters."""

    def __init__(
        self,
        side: str,
        width: float,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        height: float = 0,
        depth: float = 2,
        center: bool = False,
    ):
        """This method will initialize a hole that is not round.
        The location refers to its top left hand corner."""
        Location.__init__(self, x, y, z, side)
        self.x_size = width
        self.y_size = height
        self.z_size = depth
        self.center = center

    def export(self):
        """This method converts a RectangleCutOut to a JSON object"""
        if self.side in ["FRONT", "LEFT", "BOTTOM"]:
            self.side = None
        dict_cube = {
            "name": "cube",
            "type": "cut",
            "side": self.side,
            "x": str(self.x),
            "y": str(self.y),
            "z": str(self.z),
            # TODO: Discuss. Typically length is x, width is y, and height/depth is z.
            "x_width": str(self.x_size),
            "y_length": str(self.y_size),
            "z_depth": str(self.z_size),
            "center": self.center,
        }
        return dict_cube

    def swap_xy(self):
        """This will rotate slot while holding top where it is."""
        self.x_size, self.y_size = self.y_size, self.x_size
        Location.swap_xy(self)

    def swap_xz(self):
        """This will rotate slot while holding front where it is."""
        self.x_size, self.z_size = self.z_size, self.x_size
        Location.swap_xz(self)

    def swap_yz(self):
        """This will rotate slot while holding left where it is."""
        self.y_size, self.z_size = self.z_size, self.y_size
        Location.swap_yz(self)


class NutCutOut(Location):
    """Class for holding the data for nuts."""

    nuts = {
        "type": 3,
        "diameter": 6.01,
        "height": 2.4,
    }

    def __init__(self, side: str, x: float, y: float, z: float, nut_type: float, depth: float):
        Location.__init__(self, x, y, z, side)
        self.type = nut_type
        self.depth = depth

    def export(self):
        """Create a dictionary with the definition of a nut."""
        dict_nut = {
            "name": "nut",
            "type": "cut",
            "side": self.side,
            "x": str(self.x),
            "y": str(self.y),
            "z": str(self.z),
            "diameter": self.type,
            "depth": self.depth,
        }
        return dict_nut
