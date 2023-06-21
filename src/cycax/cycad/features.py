from cycax.cycad.location import Location


class Holes(Location):
    """This class will store data on holes. A whole will be a cylinider cut into an odject.
        This class will initialize a hole at the desired location.

    Args:
        x : The location of x along the x axis.
        y : The location of y along the y axis.
        z : The location of z along the z axis.
        side : The side of the odject that this location refers to. This will be used to specify from which side a feature should be inserted into another object. This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter : Diameter of the hole.
        depth : depth of the hole.

    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float, depth: float):
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter
        self.depth = depth

    def export(self) -> dict:
        """
        This will create a dictionary of the hole that can be used for the json.

        Returns:
            dict: this will return a dictionary.

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
        x : The location of x along the x axis.
        y : The location of y along the y axis.
        z : The location of z along the z axis.
        side : The side of the odject that this location refers to. This will be used to specify from which side a feature should be inserted into another object. This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        x_size : x_size of the rectangle.
        y_size : y_size of the rectangle.
        z_size : z_size of the rectangle.
        center : This can be over ridden to instead specify the rectangle's location from its center.

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
        """
        This will create a dictionary of the rectangle cut out that can be used for the json.

        Returns:
            dict: this will return a dictionary.

        """
        dict_cube = {}
        dict_cube["name"] = "cube"
        dict_cube["type"] = "cut"
        for key, value in vars(self).items():
            dict_cube[key] = value
        return dict_cube

    def swap_xy(self, rot: float, max_y: float):
        """
        This will rotate slot while holding top where it is. It overides the method present in the location super.

        Args:
            rot: the number of times to perfor the swap.
            max_y: the maximum value of y used for the swap.
        """
        super().swap_xy(rot=rot, max_y=max_y)
        while rot > 0:
            self.x_size, self.y_size = self.y_size, self.x_size
            rot = rot - 1

    def swap_xz(self, rot: float, max_x: float):
        """This will rotate slot while holding front where it is. It overides the method present in the location super.

        Args:
            rot: the number of times to perfor the swap.
            max_x: the maximum value of x used for the swap.
        """
        super().swap_xz(rot=rot, max_x=max_x)
        while rot > 0:
            self.x_size, self.z_size = self.z_size, self.x_size
            rot = rot - 1

    def swap_yz(self, rot: float, max_z: float):
        """This will rotate slot while holding left where it is. It overides the method present in the location super.

        Args:
            rot: the number of times to perfor the swap.
            max_z: the maximum value of z used for the swap.
        """
        super().swap_yz(rot=rot, max_z=max_z)
        while rot > 0:
            self.y_size, self.z_size = self.z_size, self.y_size
            rot = rot - 1


nut_specifications = {  # This is a global variable that will be used to cut the nuts by the OpenSCAD engine.
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
    There will be more nut information added in version 2.

    This class will initialize a Nut Cut Out at the desired location.

    Args:
        x : The location of x along the x axis.
        y : The location of y along the y axis.
        z : The location of z along the z axis.
        side : The side of the odject that this location refers to. This will be used to specify from which side a feature should be inserted into another object. This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        nut_type : Type of nut to be inserted.
        depth : depth of the rectangle.

    """

    def __init__(self, side: str, x: float, y: float, z: float, nut_type: str, depth: float):
        Location.__init__(self, x, y, z, side)
        self.nut_type = nut_type
        self.depth = depth

    def export(self) -> dict:
        """
        This will create a dictionary of the nut that can be used for the json.

        Returns:
            dict: this will return a dictionary.

        """
        dict_nut = {}
        for key, value in vars(self).items():
            dict_nut[key] = value
        dict_nut["name"] = "nut"
        dict_nut["type"] = "cut"

        return dict_nut
