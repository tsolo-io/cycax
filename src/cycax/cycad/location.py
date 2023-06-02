LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class Location:
    """This class will define the loation of an object in 3D space."""

    def __init__(self, x: float, y: float, z: float, side: str):
        self.x = x
        self.y = y
        self.z = z
        self.side = side

    def __repr__(self):
        return f"x={self.x} y={self.y} z={self.z} side={self.side}"

    def get_location(self):
        """Returns a location in a string format to be used for debugging."""
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
        self.side = {LEFT: BACK, BACK: RIGHT, RIGHT: FRONT, FRONT: LEFT, TOP: TOP, BOTTOM: BOTTOM}.get(self.side)

    def swap_xz(self, rot: float, max_x: float):
        """Rotate while holding the front where it currenly is."""
        while rot != 0:
            self.x, self.z = self.z, max_x - self.x
            rot = rot - 1
        self.side = {LEFT: BOTTOM, BOTTOM: RIGHT, RIGHT: TOP, TOP: LEFT, FRONT: FRONT, BACK: BACK}.get(self.side)

    def swap_yz(self, rot: float, max_z: float):
        """Rotate while holding the left where it currenly is."""
        while rot != 0:
            self.y, self.z = max_z - self.z, self.y
            rot = rot - 1
        self.side = {TOP: BACK, BACK: BOTTOM, BOTTOM: FRONT, FRONT: TOP, LEFT: LEFT, RIGHT: RIGHT}.get(self.side)
