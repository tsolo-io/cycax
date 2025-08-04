# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# global location variables
LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"
REAR = BACK

SIDES = (LEFT, RIGHT, TOP, BOTTOM, FRONT, BACK)


class Location:
    """The location of an object in 3D space.

    Attributes:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
    """

    def __init__(self, x: float, y: float, z: float, side: str):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.side = side

    def __repr__(self) -> str:
        return f"x={self.x} y={self.y} z={self.z} side={self.side}"

    def swap_xy(self, rot: float, rotmax: list[float]) -> list[float]:
        """Rotate while holding the top where it currently is.

        Args:
            rot: This will specify the number of times the swap is to be performed.
                This allows for it to be easier to move the objsect 180.
                As you will not need to call the method twice.
            rotmax: This is the dimensions of the object that is being rotated.

        Returns:
            New dimensions of the object.
        """

        while rot > 0:
            max_y = rotmax[1]
            self.y, self.x = self.x, max_y - self.y
            rot -= 1
            rotmax[0], rotmax[1], rotmax[2] = rotmax[1], rotmax[0], rotmax[2]
            self.side = {BACK: LEFT, RIGHT: BACK, FRONT: RIGHT, LEFT: FRONT, TOP: TOP, BOTTOM: BOTTOM}[
                self.side
            ]  # This will compute which side of the object the feature now inserts into.

        return rotmax

    def swap_xz(self, rot: float, rotmax: list[float]) -> list[float]:
        """Rotate while holding the front where it currently is.

        Args:
            rot: This will specify the number of times the swap is to be performed.
                This allows for it to be easier to move the objsect 180.
                As you will not need to call the method twice.
            rotmax: This is the dimetntions of the object that is being rotated.

        Returns:
            New dimensions of the object.
        """

        while rot > 0:
            max_x = rotmax[0]
            self.x, self.z = self.z, max_x - self.x
            rotmax[2], rotmax[1], rotmax[0] = rotmax[0], rotmax[1], rotmax[2]
            rot -= 1
            self.side = {BOTTOM: LEFT, RIGHT: BOTTOM, TOP: RIGHT, LEFT: TOP, FRONT: FRONT, BACK: BACK}[
                self.side
            ]  # This will compute which side of the object the feature now inserts into.

        return rotmax

    def swap_yz(self, rot: float, rotmax: list[float]) -> list[float]:
        """Rotate while holding the left where it currently is.

        Args:
            rot: This will specify the number of times the swap is to be performed.
                This allows for it to be easier to move the objsect 180.
                As you will not need to call the method twice.
            rotmax: This is the dimetntions of the object that is being rotated.

        Returns:
            New dimensions of the object.
        """
        while rot > 0:
            max_z = rotmax[2]
            self.y, self.z = max_z - self.z, self.y
            rotmax[0], rotmax[2], rotmax[1] = rotmax[0], rotmax[1], rotmax[2]
            rot = rot - 1
            self.side = {BACK: TOP, BOTTOM: BACK, FRONT: BOTTOM, TOP: FRONT, LEFT: LEFT, RIGHT: RIGHT}[
                self.side
            ]  # This will compute which side of the object the feature now inserts into.

        return rotmax

    def move(self, x: float | None = None, y: float | None = None, z: float | None = None):
        """Move the part from its current location on any of the axes.

        Any combination of the three arguments can be used to move the part.
        Moving in negative directions is also supported.

        Args:
            x: How much to move on the X-axis.
            y: How much to move on the Y-axis.
            z: How much to move on the Z-axis.
        """
        if x is not None:
            self.x = self.x + x
        if y is not None:
            self.y = self.y + y
        if z is not None:
            self.z = self.z + z

    def at(self, x: float | None = None, y: float | None = None, z: float | None = None):
        """Explicitly set the location of the part.

        Any combination of the three arguments can be used to set the part location.

        Args:
            x: Set location to this position on the X-axis.
            y: Set location to this position on the Y-axis.
            z: Set location to this position on the Z-axis.
        """
        if x is not None:
            self.x = x
        if y is not None:
            self.y = y
        if z is not None:
            self.z = z
