LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class location:
    """This class will define the loation of an object in 3D space"""

    def __init__(self, x: float, y: float, z: float, side: str):
        """This class will initialize a location"""
        self.x = x
        self.y = y
        self.z = z
        self.side = side

    def get_location(self):
        """Returns a location in a string format to be used for debugging"""
        return (
            " x " + str(self.x) + " y " + str(self.y) + " z " + str(self.z) + self.side
        )

    def move_x(self, x: float):
        """Moves the x varible (should be made private)"""
        self.x = x

    def move_y(self, y: float):
        """Moves the y varible (should be made private)"""
        self.y = y

    def move_z(self, z: float):
        """Moves the z varible (should be made private)"""
        self.z = z

    def at(self, x: float = 0, y: float = 0, z: float = 0):
        """This class will move a hole given a new location for it"""
        x = self.move_x(self.x + x)
        y = self.move_y(self.y + y)
        z = self.move_z(self.z + z)

    def swapXY(self, rot: float, max: float):
        """This method will rotate while holding the top where it currenly is."""
        while rot != 0:
            self.y, self.x = self.x, max - self.y
            rot = rot - 1
        if self.side == LEFT:
            self.side = BACK
        elif self.side == RIGHT:
            self.side = FRONT
        elif self.side == FRONT:
            self.side = LEFT
        elif self.side == BACK:
            self.side = RIGHT

    def swapXZ(self, rot: float, max: float):
        """This method will rotate while holding the front where it currenly is."""
        while rot != 0:
            self.x, self.z = self.z, max - self.x
            rot = rot - 1
        if self.side == LEFT:
            self.side = BOTTOM
        elif self.side == RIGHT:
            self.side = TOP
        elif self.side == TOP:
            self.side = LEFT
        elif self.side == BOTTOM:
            self.side = RIGHT

    def swapYZ(self, rot: float, max: float):
        """This method will rotate while holding the left where it currenly is."""
        while rot != 0:
            self.y, self.z = max - self.z, self.y
            rot = rot - 1
        if self.side == TOP:
            self.side = BACK
        elif self.side == BOTTOM:
            self.side = FRONT
        elif self.side == BACK:
            self.side = BOTTOM
        elif self.side == FRONT:
            self.side = TOP
