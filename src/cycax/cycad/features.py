# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import typing

from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP, Location


class Feature(Location):
    """The Parent class of all features,"""

    def __repr__(self) -> str:
        return f"Feature(name={self.name}, type={self.type}, x={self.x}, y={self.y}, z={self.z}, side={self.side})"

    def export(self) -> dict:
        """Create a dictionary holding a representation of the feature.

        Returns:
            A serialised representation of the feature.

        Raises:
            AttributeError: When name or type is not defined on the feature.
        """

        feature_dict = {}
        for key in ("name", "type"):
            getattr(self, key)  # Just get the attribute and let Python raise attribute error if it does not exists.

        for key, value in vars(self).items():
            if not key.startswith("_"):
                # Save all the public variables of the feature.
                feature_dict[key] = value

        return feature_dict


class Holes(Feature):
    """This class will store data on holes. A hole is a cylinder cut into an object.
    This class will initialize a hole at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the object that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter: Diameter of the hole.
        depth: depth of the hole.

    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float, depth: float):
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter
        self.depth = depth
        self.name = "hole"
        self.type = "cut"


class Cylinder(Feature):
    """This class will store data on cylinders. A Cylinder is added to an object.
    This class will initialize a cylinder at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the object that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter: Diameter of the cylinder.
        height: Height of the cylinder.

    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float, height: float):
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter
        self.depth = height
        self.name = "cylinder_feature"
        self.type = "add"


class RectangleCutOut(Feature):
    """This class can be used for cutting a hole that is not round but rather of the defined parameters.

    This class is a hole that is not round.
    The location refers to its bottom left hand corner.

    This class will initialize a Rectangle Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        x_size: x_size of the rectangle.
        y_size: y_size of the rectangle.
        z_size: z_size of the rectangle.
        center: This can be over ridden to instead specify the rectangle's location from its center.
    """

    def __init__(
        self,
        side: str,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        x_size: float = 0,
        z_size: float = 0,
        y_size: float = 2,
        *,
        center: bool = False,
    ):
        Location.__init__(self, x, y, z, side)
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.center = center
        self.name = "cube"
        self.type = "cut"

    def __calc__(self):
        if self.side in (FRONT, LEFT, BOTTOM):
            self.x += self.x_size / 2
            self.y += self.y_size / 2
            self.z += self.z_size / 2
        elif self.side == BACK:
            self.x += self.x_size / 2
            self.y -= self.y_size / 2
            self.z += self.z_size / 2
        elif self.side == RIGHT:
            self.x -= self.x_size / 2
            self.y += self.y_size / 2
            self.z += self.z_size / 2
        else:  # side = TOP
            self.x += self.x_size / 2
            self.y += self.y_size / 2
            self.z -= self.z_size / 2
        self.center = True

    def swap_xy(self, rot: float, rotmax: list) -> list:
        """
        This will rotate slot while holding top where it is. It overrides the method present in the location super.

        Args:
            rot: the number of times to perform the swap.
            rotmax: the maximum values for the swap.

        Returns:
            New location of relevant max of (x,y,z). useful when doing repeated swaps.
        """
        rotmax = super().swap_xy(rot=rot, rotmax=rotmax)
        while rot > 0:
            self.x_size, self.y_size = self.y_size, self.x_size
            rot = rot - 1
        return rotmax

    def swap_xz(self, rot: float, rotmax: list) -> list:
        """This will rotate slot while holding front where it is. It overrides the method present in the location super.

        Args:
            rot: the number of times to perform the swap.
            rotmax: the maximum values for the swap.

        Returns:
            New location of relevant max of (x,y,z). useful when doing repeated swaps.
        """
        rotmax = super().swap_xz(rot=rot, rotmax=rotmax)
        while rot > 0:
            self.x_size, self.z_size = self.z_size, self.x_size
            rot = rot - 1
        return rotmax

    def swap_yz(self, rot: float, rotmax: list) -> list:
        """This will rotate slot while holding left where it is. It overrides the method present in the location super.

        Args:
            rot: the number of times to perform the swap.
            rotmax: the maximum values for the swap.

        Returns:
            New location of relevant max of (x,y,z). useful when doing repeated swaps.
        """
        rotmax = super().swap_yz(rot=rot, rotmax=rotmax)
        while rot > 0:
            self.y_size, self.z_size = self.z_size, self.y_size
            rot = rot - 1

        return rotmax


class RectangleAddOn(RectangleCutOut):
    """This class can be used for cutting a hole that is not round but rather of the defined parameters.

    This class is a hole that is not round.
    The location refers to its bottom left hand corner.

    This class will initialize a Rectangle Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        x_size: x_size of the rectangle.
        y_size: y_size of the rectangle.
        z_size: z_size of the rectangle.
        center: This can be over ridden to instead specify the rectangle's location from its center.
    """

    def __init__(
        self,
        side: str,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        x_size: float = 0,
        z_size: float = 0,
        y_size: float = 2,
        *,
        center: bool = False,
    ):
        Location.__init__(self, x, y, z, side)
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.center = center
        self.name = "cube"
        self.type = "add"
        self.__calc__()

    def __calc__(self):
        if self.side in (BACK, RIGHT, TOP):
            self.x += self.x_size / 2
            self.y += self.y_size / 2
            self.z += self.z_size / 2
        elif self.side == FRONT:
            self.x += self.x_size / 2
            self.y -= self.y_size / 2
            self.z += self.z_size / 2
        elif self.side == LEFT:
            self.x -= self.x_size / 2
            self.y += self.y_size / 2
            self.z += self.z_size / 2
        else:  # side = BOTTOM
            self.x += self.x_size / 2
            self.y += self.y_size / 2
            self.z -= self.z_size / 2
        self.center = True


class NutCutOut(Feature):
    """
    Class for holding the data for nut cut outs.
    The nut cut outs will allow us to hold nuts in 3D printed plastic.

    This class will initialize a Nut Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        nut_type: Type of nut to be inserted.
        depth: depth of the nut.
        vertical: this is a bool that will be set to False if you want the flat side down.
    """

    nut_specifications: typing.ClassVar[
        dict[str, dict[str, float]]
    ] = {  # This is a global variable that will be used to cut the nuts by the OpenSCAD engine.
        "M3ISO": {
            "diameter": 6.01,
            "thickness": 2.4,
            "side_to_side": 5.4,
        },
        "M3": {
            "diameter": 6.2,
            "thickness": 2.5,
            "side_to_side": 5.5,
        },
        "M6ISO": {
            "diameter": 11.05,
            "thickness": 5.2,
            "side_to_side": 10,
        },
    }

    def __init__(
        self,
        side: str,
        x: float,
        y: float,
        z: float,
        nut_type: str,
        depth: float | None = None,
        *,
        vertical: bool = True,
    ):
        self.name = "nut"
        self.type = "cut"
        Location.__init__(self, x, y, z, side)
        self.nut_type = nut_type.upper()
        self.diameter = NutCutOut.nut_specifications[self.nut_type]["diameter"]
        self.thickness = NutCutOut.nut_specifications[self.nut_type]["thickness"]
        self.side_to_side = NutCutOut.nut_specifications[self.nut_type]["side_to_side"]
        if depth is None:
            self.depth = self.thickness
        else:
            self.depth = depth
        self.vertical = vertical


class SphereCutOut(Feature):
    """
    Class for holding the data for sphere cut outs.

    This class will initialize a Sphere Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter: diameter of the sphere.
    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float):
        self.name = "sphere"
        self.type = "cut"
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter


class SphereAdd(Feature):
    """
    Class for holding the data for sphere cut outs.

    This class will initialize a Sphere Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter: diameter of the sphere.
    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float):
        self.name = "sphere"
        self.type = "add"
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter
