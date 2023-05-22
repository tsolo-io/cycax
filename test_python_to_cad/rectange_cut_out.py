from location import location


class rectangle_cut_out(location):
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
        location.__init__(self, x, y, z, side)
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
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "X_width": self.x_size,
            "Y_length": self.y_size,
            "Z_depth": self.z_size,
            "center": self.center,
        }
        return dict_cube

    def swapXY(self):
        """This will rotate slot while holding top where it is."""
        self.x_size, self.y_size = self.y_size, self.x_size
        location.swapXY(self)

    def swapXZ(self):
        """This will rotate slot while holding front where it is."""
        self.x_size, self.z_size = self.z_size, self.x_size
        location.swapXZ(self)

    def swapYZ(self):
        """This will rotate slot while holding left where it is."""
        self.y_size, self.z_size = self.z_size, self.y_size
        location.swapYZ(self)
