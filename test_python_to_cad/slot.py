from location import location
from holes import holes
from rectange_cut_out import rectangle_cut_out


class slot:
    hole_left: holes
    hole_right: holes
    rectangle: rectangle_cut_out
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
        Horizontal: bool = True,
    ):
        """This method will be used to define a slot with all ist parameters. To get a verticle slot enter the details in exactly the same manner to the horizontle slot and the specify that Horrizontal to False."""
        if Horizontal:
            self.hole_left = holes(side=side, x=x, y=y, z=z, big=y_size, depth=z_size)
            self.hole_right = holes(
                side=side, x=x + x_size, y=y, z=z, big=y_size, depth=z_size
            )
            self.rectangle = rectangle_cut_out(
                side=side, width=x_size, x=x, y=y, z=z, height=y_size, depth=z_size
            )
        else:
            self.hole_left = holes(side=side, x=x, y=y, z=z, big=y_size, depth=z_size)
            self.hole_right = holes(
                side=side, x=x, y=y + y_size, z=z, big=y_size, depth=z_size
            )
            self.rectangle = rectangle_cut_out(
                side=side, width=y_size, x=x, y=y, z=z, height=x_size, depth=z_size
            )

    def export(self):
        """This will be used to create a dict of the slot."""
        dict_hole_left = self.hole_left.export()
        dict_hole_right = self.hole_right.export()
        dict_rectangle = self.rectangle.export()

        return dict_hole_left, dict_hole_right, dict_rectangle

    def move(self, x: float = 0, y: float = 0, z: float = 0):
        """This class will move a hole given a new location for it The location refers to its top left hand corner."""
        self.hole_left.at(x, y, z)
        self.hole_right.at(x, y, z)
        self.rectangle.at(x, y, z)