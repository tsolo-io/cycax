# global location variables
LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"
REAR = "BACK"


class Location:
    """This class will define the loation of an object in 3D space.
    This class will initialize a location along the x, y, z axis.

    Args:
        x : The location of x along the x axis.
        y : The location of y along the y axis.
        z : The location of z along the z axis.
        side : The side of the odject that this location refers to. This will be used to specify from which side a feature should be inserted into another object. This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
    """

    def __init__(self, x: float, y: float, z: float, side: str):
        self.x = x
        self.y = y
        self.z = z
        self.side = side

    def __repr__(self) -> str:
        return f"x={self.x} y={self.y} z={self.z} side={self.side}"

    def swap_xy(self, rot: float, max_y: float):
        """Rotate while holding the top where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_y: This is the maximium value of the object on the y axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        while rot != 0:
            self.y, self.x = self.x, max_y - self.y
            rot = rot - 1
        self.side = {LEFT: BACK, BACK: RIGHT, RIGHT: FRONT, FRONT: LEFT, TOP: TOP, BOTTOM: BOTTOM}[self.side] # This will compute which side of the object the feature now inserts into.

    def swap_xz(self, rot: float, max_x: float):
        """Rotate while holding the front where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_x: This is the maximium value of the object on the x axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        while rot != 0:
            self.x, self.z = self.z, max_x - self.x
            rot = rot - 1
        self.side = {LEFT: BOTTOM, BOTTOM: RIGHT, RIGHT: TOP, TOP: LEFT, FRONT: FRONT, BACK: BACK}[self.side]  # This will compute which side of the object the feature now inserts into.
        
    def move(self, x: float=None, y: float=None, z: float=None):
        """This move can be used to translate objects based on the provided arguments.
        Args:
            x: the value to which x needs to be moved.
            y: the value to which y needs to be moved.
            z: the value to which z needs to be moved.
        """
        if x is not None:
            self.x=x
        if y is not None:
            self.y=y
        if z is not None:
            self.z=z

    def swap_yz(self, rot: float, max_z: float):
        """Rotate while holding the left where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_z: This is the maximium value of the object on the z axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        while rot != 0:
            self.y, self.z = max_z - self.z, self.y
            rot = rot - 1
        self.side = {TOP: BACK, BACK: BOTTOM, BOTTOM: FRONT, FRONT: TOP, LEFT: LEFT, RIGHT: RIGHT}[self.side]  # This will compute which side of the object the feature now inserts into.
