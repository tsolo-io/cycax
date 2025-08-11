# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad.assembly import Assembly
from cycax.cycad.cycad_part import CycadPart
from cycax.cycad.location import BOTTOM

# TODO(MJ): Rename this file.


class Cylinder(CycadPart):
    """
    This method will initialize a Cylinder.
    """

    def __init__(
        self,
        part_no: str,
        diameter: float,
        height: float,
        assembly: Assembly | None = None,
        colour: str = "pink",
    ):
        self.x_center = diameter / 2
        self.y_center = diameter / 2
        self.z_center = height / 2
        self.radius = diameter / 2
        self.diameter = diameter
        super().__init__(
            x=0.0,  # Origin is outside of the cylinder.
            y=0.0,  # Origin is outside of the cylinder.
            z=0.0,  # Origin is outside of the cylinder.
            side=BOTTOM,
            part_no=part_no,
            x_size=diameter,
            y_size=diameter,
            z_size=height,
            assembly=assembly,
            colour=colour,
            polygon="cylinder",
        )  # initializes the cylinder to (0,0,0)


class Cuboid(CycadPart):
    """
    This method will initialize a Cuboid of a specific size.

    Args:
        x_size : The size of x.
        y_size : The size of y.
        z_size : The size of z.
        part_no : The unique name that will be given to a type of parts.
        colour: This will specify the colour of the object and can be overwritten from red.
        assembly: The assembly the part belongs to.
    """

    def __init__(
        self,
        part_no: str,
        x_size: float,
        y_size: float,
        z_size: float,
        assembly: Assembly | None = None,
        colour: str = "pink",
    ):
        super().__init__(
            x=0.0,
            y=0.0,
            z=0.0,
            side=BOTTOM,
            part_no=part_no,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
            assembly=assembly,
            colour=colour,
            polygon="cube",
        )  # initializes the cuboid to (0,0,0)


class SheetMetal(Cuboid):
    """
    This class will initialize a sheetmetal part at the location (0,0,0).

    Args:
        x_size : The size of x.
        y_size : The size of y.
        z_size : The size of z.
        part_no : The unique name that will be given to a type of parts.
        assembly: The assembly the part belongs to.
    """

    def __init__(
        self, part_no: str, x_size: float, y_size: float, z_size: float = 2.0, assembly: Assembly | None = None
    ):
        super().__init__(part_no=part_no, x_size=x_size, y_size=y_size, z_size=z_size, colour="gray", assembly=assembly)


class Print3D(Cuboid):
    """
    This class will initialize a 3D Print part at the location (0,0,0).

    Args:
        x_size : The size of x.
        y_size : The size of y.
        z_size : The size of z.
        part_no : The unique name that will be given to a type of parts.
        assembly: The assembly the part belongs to.
    """

    def __init__(self, part_no: str, x_size: float, y_size: float, z_size: float, assembly: Assembly | None = None):
        super().__init__(part_no=part_no, x_size=x_size, y_size=y_size, z_size=z_size, colour="red", assembly=assembly)
