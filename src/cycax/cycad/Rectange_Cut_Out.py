from Location import Location


class Rectangle_Cut_Out(Location):
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
        """This method will initialize a hole that is not round. The location refers to its top left hand corner."""
        Location.__init__(self, x, y, z, side)
        self.x_size = width
        self.y_size = height
        self.z_size = depth
        self.center = center

    def export(self):
        """This method converts a RectangleCutOut to a json dictionary"""
        if self.side == "FRONT" or self.side == "LEFT" or self.side == "BOTTOM":
            self.side = None
        dict_cube = {
            "name": "cube",
            "type": "cut",
            "side": self.side,
            "x": str(self.x),
            "y": str(self.y),
            "z": str(self.z),
            "X_width": str(self.x_size),
            "Y_length": str(self.y_size),
            "Z_depth": str(self.z_size),
            "center": self.center,
        }
        return dict_cube

    def swapXY(self):
        """This will rotate slot while holding top where it is."""
        self.x_size, self.y_size = self.y_size, self.x_size
        Location.swapXY(self)

    def swapXZ(self):
        """This will rotate slot while holding front where it is."""
        self.x_size, self.z_size = self.z_size, self.x_size
        Location.swapXZ(self)

    def swapYZ(self):
        """This will rotate slot while holding left where it is."""
        self.y_size, self.z_size = self.z_size, self.y_size
        Location.swapYZ(self)
