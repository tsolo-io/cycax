# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad.features import Holes, RectangleCutOut
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class Slot:
    """A slot with parameters.

    To get a vertical slot enter the details in exactly the same manner to
    the horizontal slot and then specify that horizontal to False.

    This class will initialize a slot in the desired location.

    Attributes:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        x_size: The location of x_size of slot.
        y_size: The location of y_size of slot.
        z_size: The location of z_size of slot.
        horizontal: This can be overridden if you need a vertical slot.

    """

    # TODO: Class docstring and order of init attributes do not match. The docstring looks more sensible.
    def __init__(
        self,
        side: str,
        x_size: float,
        y_size: float,
        z_size: float,
        x: float,
        y: float,
        z: float,
        *,
        horizontal: bool = True,
    ):
        if side is TOP:
            if horizontal:
                self.hole_left = Holes(side=side, x=x + y_size / 2, y=y, z=z, diameter=y_size, depth=z_size)
                self.hole_right = Holes(side=side, x=x + x_size - y_size / 2, y=y, z=z, diameter=y_size, depth=z_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x + y_size / 2,
                    y=y - y_size / 2,
                    z=z,
                    x_size=x_size - y_size,
                    y_size=y_size,
                    z_size=z_size,
                )
                self.rectangle.__calc__()

            else:
                self.hole_left = Holes(side=side, x=x, y=y + x_size / 2, z=z, diameter=x_size, depth=z_size)
                self.hole_right = Holes(side=side, x=x, y=y + y_size - x_size / 2, z=z, diameter=x_size, depth=z_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x - x_size / 2,
                    y=y + x_size / 2,
                    z=z,
                    x_size=x_size,
                    y_size=y_size - x_size,
                    z_size=z_size,
                )
                self.rectangle.__calc__()

        if side is BOTTOM:
            if horizontal:
                self.hole_left = Holes(side=side, x=x + y_size / 2, y=y, z=z, diameter=y_size, depth=z_size)
                self.hole_right = Holes(side=side, x=x + x_size - y_size / 2, y=y, z=z, diameter=y_size, depth=z_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x + y_size / 2,
                    y=y - y_size / 2,
                    z=z,
                    x_size=x_size - y_size,
                    y_size=y_size,
                    z_size=z_size,
                )
                self.rectangle.__calc__()

            else:
                self.hole_left = Holes(side=side, x=x, y=y - x_size / 2, z=z, diameter=x_size, depth=z_size)
                self.hole_right = Holes(side=side, x=x, y=y - y_size + x_size / 2, z=z, diameter=x_size, depth=z_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x - x_size / 2,
                    y=y - y_size + x_size / 2,
                    z=z,
                    x_size=x_size,
                    y_size=y_size - x_size,
                    z_size=z_size,
                )
                self.rectangle.__calc__()

        if side is FRONT:
            if horizontal:
                self.hole_left = Holes(side=side, x=x + z_size / 2, y=y, z=z, diameter=z_size, depth=y_size)
                self.hole_right = Holes(side=side, x=x + x_size - z_size / 2, y=y, z=z, diameter=z_size, depth=y_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x + z_size / 2,
                    y=y,
                    z=z - z_size / 2,
                    x_size=x_size - z_size,
                    y_size=y_size,
                    z_size=z_size,
                )
                self.rectangle.__calc__()

            else:
                self.hole_left = Holes(side=side, x=x, y=y, z=z + x_size / 2, diameter=x_size, depth=y_size)
                self.hole_right = Holes(side=side, x=x, y=y, z=z - x_size / 2 + z_size, diameter=x_size, depth=y_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x - x_size / 2,
                    y=y,
                    z=z + x_size / 2,
                    x_size=x_size,
                    y_size=y_size,
                    z_size=z_size - x_size,
                )
                self.rectangle.__calc__()

        if side is BACK:
            if horizontal:
                self.hole_left = Holes(side=side, x=x - z_size / 2, y=y, z=z, diameter=z_size, depth=y_size)
                self.hole_right = Holes(side=side, x=x - x_size + z_size / 2, y=y, z=z, diameter=z_size, depth=y_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x - x_size + z_size / 2,
                    y=y,
                    z=z - z_size / 2,
                    x_size=x_size - z_size,
                    y_size=y_size,
                    z_size=z_size,
                )
                self.rectangle.__calc__()

            else:
                self.hole_left = Holes(side=side, x=x, y=y, z=z + x_size / 2, diameter=x_size, depth=y_size)
                self.hole_right = Holes(side=side, x=x, y=y, z=z - x_size / 2 + z_size, diameter=x_size, depth=y_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x - x_size / 2,
                    y=y,
                    z=z + x_size / 2,
                    x_size=x_size,
                    y_size=y_size,
                    z_size=z_size - x_size,
                )
                self.rectangle.__calc__()

        if side is RIGHT:
            if horizontal:
                self.hole_left = Holes(side=side, x=x, y=y + z_size / 2, z=z, diameter=z_size, depth=x_size)
                self.hole_right = Holes(side=side, x=x, y=y + y_size - z_size / 2, z=z, diameter=z_size, depth=x_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x,
                    y=y + z_size / 2,
                    z=z - z_size / 2,
                    x_size=x_size,
                    y_size=y_size - z_size,
                    z_size=z_size,
                )
                self.rectangle.__calc__()

            else:
                self.hole_left = Holes(side=side, x=x, y=y, z=z + y_size / 2, diameter=y_size, depth=x_size)
                self.hole_right = Holes(side=side, x=x, y=y, z=z + z_size - y_size / 2, diameter=y_size, depth=x_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x,
                    y=y - y_size / 2,
                    z=z + y_size / 2,
                    x_size=x_size,
                    y_size=y_size,
                    z_size=z_size - y_size,
                )
                self.rectangle.__calc__()

        if side is LEFT:
            if horizontal:
                self.hole_left = Holes(side=side, x=x, y=y - z_size / 2, z=z, diameter=z_size, depth=x_size)
                self.hole_right = Holes(side=side, x=x, y=y - y_size + z_size / 2, z=z, diameter=z_size, depth=x_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x,
                    y=y - y_size + z_size / 2,
                    z=z - z_size / 2,
                    x_size=x_size,
                    y_size=y_size - z_size,
                    z_size=z_size,
                )
                self.rectangle.__calc__()

            else:
                self.hole_left = Holes(side=side, x=x, y=y, z=z + y_size / 2, diameter=y_size, depth=x_size)
                self.hole_right = Holes(side=side, x=x, y=y, z=z + z_size - y_size / 2, diameter=y_size, depth=x_size)
                self.rectangle = RectangleCutOut(
                    side=side,
                    x=x,
                    y=y - y_size / 2,
                    z=z + y_size / 2,
                    x_size=x_size,
                    y_size=y_size,
                    z_size=z_size - y_size,
                )
                self.rectangle.__calc__()
