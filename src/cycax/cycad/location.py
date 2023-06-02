LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class Location:
    """This class will define the loation of an object in 3D space"""

    def __init__(self, x: float, y: float, z: float, side: str):
        """This class will initialize a location"""
        self.x = x
        self.y = y
        self.z = z
        self.side = side

    def __repr__(self):
        return f"x={self.x} y={self.y} z={self.z} side={self.side}"

    def get_location(self):
        """Returns a location in a string format to be used for debugging"""
        # TODO: Remove. Rather use __repr__ or __str__ methods.
        return f"x={self.x} y={self.y} z={self.z} side={self.side}"

    def move(self, x: float = 0, y: float = 0, z: float = 0):
        """Update position relative to its current location.

        Args:
            x: Move this many units on the X-axis.
            y: Move this many units on the Y-axis.
            z: Move this many units on the Z-axis.
        """
        self.x = self.x + x
        self.y = self.y + y
        self.z = self.z + z

    def at(self, x: float = 0, y: float = 0, z: float = 0):
        """This class will move a location to the exact location provided."""
        self.x = x
        self.y = y
        self.z = z

    def swap_xy(self, rot: float, max_y: float):
        """Rotate while holding the top where it currenly is."""
        while rot != 0:
            self.y, self.x = self.x, max_y - self.y
            rot = rot - 1
        if self.side == LEFT:
            self.side = BACK
        elif self.side == RIGHT:
            self.side = FRONT
        elif self.side == FRONT:
            self.side = LEFT
        elif self.side == BACK:
            self.side = RIGHT

    def swap_xz(self, rot: float, max_x: float):
        """Rotate while holding the front where it currenly is."""
        while rot != 0:
            self.x, self.z = self.z, max_x - self.x
            rot = rot - 1
        if self.side == LEFT:
            self.side = BOTTOM
        elif self.side == RIGHT:
            self.side = TOP
        elif self.side == TOP:
            self.side = LEFT
        elif self.side == BOTTOM:
            self.side = RIGHT

    def swap_yz(self, rot: float, max_z: float):
        """Rotate while holding the left where it currenly is."""
        while rot != 0:
            self.y, self.z = max_z - self.z, self.y
            rot = rot - 1
        if self.side == TOP:
            self.side = BACK
        elif self.side == BOTTOM:
            self.side = FRONT
        elif self.side == BACK:
            self.side = BOTTOM
        elif self.side == FRONT:
            self.side = TOP

    def side_location_calculator(self, side: str, x: float, y: float, sink=0) -> tuple[float, float, float]:
        """Calculate given the side of and object and the relative x and y location on that side where the definite location is."""

        if side == TOP:
            temp_x = x
            temp_y = y
            temp_z = self.z_max - sink  # Where is self.z_max defined??
        elif side == BOTTOM:
            temp_x = x
            temp_y = y
            temp_z = self.z_min + sink
        elif side == LEFT:
            temp_x = self.x_min + sink
            temp_y = x
            temp_z = y
        elif side == RIGHT:
            temp_x = self.x_max - sink
            temp_y = x
            temp_z = y
        elif side == FRONT:
            temp_x = x
            temp_y = self.y_min + sink
            temp_z = y
        elif side == BACK:
            temp_x = x
            temp_y = self.y_max - sink
            temp_z = y
        else:
            msg = f"Side {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
            raise ValueError(msg)

        return temp_x, temp_y, temp_z
