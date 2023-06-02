# global location variables
LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class Location:
    """This class will define the loation of an object in 3D space."""

    def __init__(self, x: float, y: float, z: float, side: str):
        """
        This method will initialize a location along the x, y, z axis.

        Args:
            x : The location of x along the x axis.
            y : The location of y along the y axis.
            z : The location of z along the z axis.
            side : The side of the odject that this location refers to. This will be used to specify from which side a feature should be inserted into another object. This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        """
        self.x = x
        self.y = y
        self.z = z
        self.side = side

    def __repr__(self):
        """
        Returns a location in a string format to be used for debugging.

        Returns:
            str: this method will return a string which will specify the current location of an object.
        """
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
        """This class will move a location to the exact location provided.

        Args:
            x: Move to this exact location on the X-axis.
            y: Move to this exact location on the Y-axis.
            z: Move to this exact location on the Z-axis.
        """
        self.x = x
        self.y = y
        self.z = z

    def swap_xy(self, rot: float, max_y: float):
        """Rotate while holding the top where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_y: This is the maximium value of the object on the y axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        while rot != 0:
            self.y, self.x = self.x, max_y - self.y
            rot = rot - 1
        self.side = {LEFT: BACK, BACK: RIGHT, RIGHT: FRONT, FRONT: LEFT, TOP: TOP, BOTTOM: BOTTOM}.get(self.side)  #This will compute which side of the object the feature now inserts into.

    def swap_xz(self, rot: float, max_x: float):
        """Rotate while holding the front where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_x: This is the maximium value of the object on the x axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        while rot != 0:
            self.x, self.z = self.z, max_x - self.x
            rot = rot - 1
        self.side = {LEFT: BOTTOM, BOTTOM: RIGHT, RIGHT: TOP, TOP: LEFT, FRONT: FRONT, BACK: BACK}.get(self.side) #This will compute which side of the object the feature now inserts into.

    def swap_yz(self, rot: float, max_z: float):
        """Rotate while holding the left where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_z: This is the maximium value of the object on the z axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        while rot != 0:
            self.y, self.z = max_z - self.z, self.y
            rot = rot - 1
        self.side = {TOP: BACK, BACK: BOTTOM, BOTTOM: FRONT, FRONT: TOP, LEFT: LEFT, RIGHT: RIGHT}.get(self.side) #This will compute which side of the object the feature now inserts into.
