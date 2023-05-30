from Cuboid import Cuboid

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class Con_Cube(Cuboid):
    """This class holds the data for the corner cube."""

    def __init__(self):
        Cuboid.__init__(self, part_no="con_cube", x_size=11, y_size=11, z_size=11)
        self.calculate()

    def calculate(self):
        """Calculate the concube."""
        for side in (LEFT, BOTTOM, FRONT):
            self.make_hole(x=7, y=7, side=side, diameter=3.2, depth=2, Inner=False)
            self.make_hole(
                x=7, y=7, side=side, diameter=2.9, depth=11, Inner=True
            )  # Through everything
            self.make_nut(
                side=side, x=7, y=7, type=3, depth=2, sink=1
            )  # Coordinates based on center of the Nut.

            # # Two holes for the bolt. The bolt go into a slightly bigger hole, then through the nut then a tight hole to act like a thread lock.

        self.make_rectangle(
            side=LEFT, x=7, y=10, height=6.2, width=2, depth=3, sink=2, center=True
        )
        self.make_rectangle(
            side=BOTTOM, x=7, y=10, height=3, width=6.2, depth=2, sink=2, center=True
        )
        self.make_rectangle(
            side=FRONT, x=7, y=10, height=2, width=6.2, depth=3, sink=2, center=True
        )

        # Cut the excess material we dont want to print.
        self.make_rectangle(TOP, x=11, y=4, height=7, width=7, depth=7)
