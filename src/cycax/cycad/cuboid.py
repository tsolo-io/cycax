from cycax.cycad.cycad_part import CycadPart


class Cuboid(CycadPart):
    """
    This class will contain information on the 3D printed part.
    This method will initialize a Cuboid at the desired location.

    Args:
        x_size : The size of x.
        y_size : The size of y.
        z_size : The size of z.
        part_no : The unique name that will be given to a type of parts.
        colour: This will specify the colour of the object and can be overwritten from red.

    """

    def __init__(self, part_no: str, x_size: float, y_size: float, z_size: float, colour: str = "pink"):
        super().__init__(
            x=0,
            y=0,
            z=0,
            side=None,
            part_no=part_no,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
            colour=colour,
            polygon="cube",
        )  # initializes the cuboid to (0,0,0)


class SheetMetal(Cuboid):
    """
    This class will initialize a sheetmetal part at the  location (0,0,0).

    Args:
        x_size : The size of x.
        y_size : The size of y.
        z_size : The size of z.
        part_no : The unique name that will be given to a type of parts.
    """

    def __init__(self, part_no: str, x_size: float, y_size: float, z_size: float = 2.0):
        super().__init__(part_no=part_no, x_size=x_size, y_size=y_size, z_size=z_size, colour="grey")


class Print3D(Cuboid):
    """
    This class will initialize a 3DPrint part at the  location (0,0,0).

    Args:
        x_size : The size of x.
        y_size : The size of y.
        z_size : The size of z.
        part_no : The unique name that will be given to a type of parts.
    """

    def __init__(self, part_no: str, x_size: float, y_size: float, z_size: float):
        super().__init__(part_no=part_no, x_size=x_size, y_size=y_size, z_size=z_size, colour="red")
