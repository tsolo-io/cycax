from cycax.cycad.features import Holes, RectangleCutOut


class Slot:
    """A slot with parameters.

    To get a verticle slot enter the details in exactly the same manner to
    the horizontle slot and then specify that horrizontal to False."""
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
            self.hole_left = Holes(side=side, x=x, y=y, z=z, big=y_size, depth=z_size)
            self.hole_right = Holes(side=side, x=x + x_size, y=y, z=z, big=y_size, depth=z_size)
            self.rectangle = RectangleCutOut(side=side, width=x_size, x=x, y=y, z=z, height=y_size, depth=z_size)
        else:
            self.hole_left = Holes(side=side, x=x, y=y, z=z, big=y_size, depth=z_size)
            self.hole_right = Holes(side=side, x=x, y=y + y_size, z=z, big=y_size, depth=z_size)
            self.rectangle = RectangleCutOut(side=side, width=y_size, x=x, y=y, z=z, height=x_size, depth=z_size)

    def export(self):
        """This will be used to create a dict of the slot."""
        dict_hole_left = self.hole_left.export()
        dict_hole_right = self.hole_right.export()
        dict_rectangle = self.rectangle.export()

        return dict_hole_left, dict_hole_right, dict_rectangle

    def move(self, x: float = 0, y: float = 0, z: float = 0):
        """Move to a new location,
        the location refers to its top left hand corner."""
        self.hole_left.move(x, y, z)
        self.hole_right.move(x, y, z)
        self.rectangle.move(x, y, z)
