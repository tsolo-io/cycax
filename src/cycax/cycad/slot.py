from cycax.cycad.features import Holes, RectangleCutOut


class Slot:
    """A slot with parameters.

    To get a verticle slot enter the details in exactly the same manner to
    the horizontle slot and then specify that horrizontal to False.

    This class will initialize a slot in the desired location.

    Args:
        x : The location of x along the x axis.
        y : The location of y along the y axis.
        z : The location of z along the z axis.
        side : The side of the odject that this location refers to. This will be used to specify from which side a feature should be inserted into another object. This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        x_size : The location of x_size of slot.
        y_size : The location of y_size of slot.
        z_size : The location of z_size of slot.
        horizontal: This can be overridden it you need a verticle slot.

    """

    def __init__(
        self,
        side: str,
        x_size: float,
        y_size: float,
        z_size: float,
        x: float,
        y: float,
        z: float,
        horizontal: bool = True,
    ):
        if horizontal:
            self.hole_left = Holes(side=side, x=x + y_size / 2, y=y, z=z, diameter=y_size, depth=z_size)
            self.hole_right = Holes(side=side, x=x + x_size - y_size / 2, y=y, z=z, diameter=y_size, depth=z_size)
            self.rectangle = RectangleCutOut(
                side=side, x=x + y_size / 2, y=y - y_size / 2, z=z, x_size=x_size - y_size, y_size=y_size, z_size=z_size
            )

        else:
            self.hole_left = Holes(side=side, x=x, y=y + x_size / 2, z=z, diameter=x_size, depth=z_size)
            self.hole_right = Holes(side=side, x=x, y=y + y_size - x_size / 2, z=z, diameter=x_size, depth=z_size)
            self.rectangle = RectangleCutOut(
                side=side, x=x - x_size / 2, y=y + x_size / 2, z=z, x_size=x_size, y_size=y_size - x_size, z_size=z_size
            )

    def export(self) -> tuple:
        """
        This will create a dictionary of the slot that can be used for the json.

        Returns:
            tpl: this will return a tupple of dictionaries. This needs to be changed to releasing dictionarties.

        """
        dict_hole_left = self.hole_left.export()
        dict_hole_right = self.hole_right.export()
        dict_rectangle = self.rectangle.export()

        return dict_hole_left, dict_hole_right, dict_rectangle

    def swap_xy(self, rot: float, max_y: float):
        """Rotate while holding the top where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_y: This is the maximium value of the object on the y axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        self.hole_left.swap_xy(rot=rot, max_y=max_y)
        self.hole_right.swap_xy(rot=rot, max_y=max_y)
        self.rectangle.swap_xy(rot=rot, max_y=max_y)

    def swap_xz(self, rot: float, max_x: float):
        """Rotate while holding the front where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_x: This is the maximium value of the object on the x axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        self.hole_left.swap_xz(rot=rot, max_x=max_x)
        self.hole_right.swap_xz(rot=rot, max_x=max_x)
        self.rectangle.swap_xz(rot=rot, max_x=max_x)

    def swap_yz(self, rot: float, max_z: float):
        """Rotate while holding the left where it currenly is.

        Args:
            rot: This will specify the number of times the swap is to be performed. This allows for it to be easier to move the objsect 180. as you will not need to call the method twice.
            max_z: This is the maximium value of the object on the z axis. This is used as a metric to move the value once swapped back into the quadrant it came from. In this manner if performs bot a rotate and a translate back to its original quadrant.

        """
        self.hole_left.swap_yz(rot=rot, max_z=max_z)
        self.hole_right.swap_yz(rot=rot, max_z=max_z)
        self.rectangle.swap_yz(rot=rot, max_z=max_z)
