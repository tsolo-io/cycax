from cycax.cycad.location import Location


class Holes(Location):
    """This class will store data on holes. A whole will be a cylinider cut into an odject.
    This class will initialize a hole at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter: Diameter of the hole.
        depth: depth of the hole.

    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float, depth: float):
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter
        self.depth = depth

    def export(self) -> dict:
        """This will create a dictionary of the hole that can be used for the JSON.

        Returns:
            this will return a dictionary.
        """

        dict_hole = {}
        dict_hole["name"] = "hole"
        dict_hole["type"] = "cut"
        for key, value in vars(self).items():
            dict_hole[key] = value
        return dict_hole


class RectangleCutOut(Location):
    """This class can be used for cutting a hole that is not round but rather of the definied parameters.

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
        center: bool = False,
    ):
        Location.__init__(self, x, y, z, side)
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.center = center

    def export(self) -> dict:
        """This will create a dictionary of the rectangle cut out that can be used for the JSON.

        Returns:
            This will return a dictionary.
        """
        dict_cube = {}
        dict_cube["name"] = "cube"
        dict_cube["type"] = "cut"
        for key, value in vars(self).items():
            dict_cube[key] = value
        return dict_cube

    def swap_xy(self, rot: float, rotmax: list) -> list:
        """
        This will rotate slot while holding top where it is. It overides the method present in the location super.

        Args:
            rot: the number of times to perfor the swap.
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
        """This will rotate slot while holding front where it is. It overides the method present in the location super.

        Args:
            rot: the number of times to perfor the swap.
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
        """This will rotate slot while holding left where it is. It overides the method present in the location super.

        Args:
            rot: the number of times to perfor the swap.
            rotmax: the maximum values for the swap.

        Returns:
            New location of relevant max of (x,y,z). useful when doing repeated swaps.
        """
        rotmax = super().swap_yz(rot=rot, rotmax=rotmax)
        while rot > 0:
            self.y_size, self.z_size = self.z_size, self.y_size
            rot = rot - 1
        return rotmax


nut_specifications: dict[
    str, dict[str, float]
] = {  # This is a global variable that will be used to cut the nuts by the OpenSCAD engine.
    "M3": {
        "diameter": 6.01,
        "thickness": 2.4,
    },
    "M6": {
        "diameter": 11.05,
        "thickness": 5.2,
    },
}


class NutCutOut(Location):
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
        depth: depth of the rectangle.
        vertical: this is a bool that will be set to False if you want the flat side down.
    """

    def __init__(self, side: str, x: float, y: float, z: float, nut_type: str, depth: float, vertical: bool = True):
        Location.__init__(self, x, y, z, side)
        self.nut_type = nut_type.upper()
        self.diameter = nut_specifications[self.nut_type]["diameter"]
        self.thickness = nut_specifications[self.nut_type]["thickness"]
        self.depth = depth
        self.vertical = vertical

    def export(self) -> dict:
        """This will create a dictionary of the nut that can be used for the JSON.

        Returns:
            this will return a dictionary.
        """
        dict_nut = {}
        for key, value in vars(self).items():
            dict_nut[key] = value
        dict_nut["name"] = "nut"
        dict_nut["type"] = "cut"

        return dict_nut
    

class SphereCutOut(Location):
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
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter

    def export(self) -> dict:
        """This will create a dictionary of the sphere that can be used for the JSON.

        Returns:
            this will return a dictionary.
        """
        dict_sphere = {}
        for key, value in vars(self).items():
            dict_sphere[key] = value
        dict_sphere["name"] = "sphere"
        dict_sphere["type"] = "cut"

        return dict_sphere
