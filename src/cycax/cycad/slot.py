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

    hole_left: Holes
    hole_right: Holes
    rectangle: RectangleCutOut
    depth: float = 2

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
            self.hole_left = Holes(side=side, x=x+y_size, y=y, z=z, diameter=y_size, depth=z_size)
            self.hole_right = Holes(side=side, x=x + x_size, y=y, z=z, diameter=y_size, depth=z_size)
            self.rectangle = RectangleCutOut(side=side, x=x + x_size, y=y-y_size/2, z=z, x_size=x_size-y_size, y_size=y_size, z_size=z_size)
           
        else:
            self.hole_left = Holes(side=side, x=x, y=y, z=z, diameter=y_size/2, depth=z_size)
            self.hole_right = Holes(side=side, x=x, y=y + y_size, z=z, diameter=y_size/2, depth=z_size)
            self.rectangle = RectangleCutOut(side=side, x=x, y=y, z=z, x_size=y_size, y_size=x_size, z_size=z_size)
            

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

    def move(self, x: float = 0, y: float = 0, z: float = 0):
        """
        Move to a new location, the location refers to its top left hand corner.
        Args:
            x: move this x this many units along the x axis.
            y: move this y this many units along the y axis.
            z: move this z this many units along the z axis.
        """

        self.hole_left.move(x, y, z)
        self.hole_right.move(x, y, z)
        self.rectangle.move(x, y, z)
