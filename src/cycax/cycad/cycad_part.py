from cycax.cycad.features import Holes, NutCutOut, RectangleCutOut
from cycax.cycad.location import TOP, Location
from cycax.cycad.slot import Slot


class CycadPart(Location):
    def __init__(
        self,
        part_no: str,
        x_size: float,
        y_size: float,
        z_size: float,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        side: str = TOP,
    ):
        super().__init__(x, y, z, side)
        self.part_no = part_no
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.features = []  # Stores all the holes to be cut
        self.move_holes = []
        self.x_max: float = self.x_size  # Location.Right
        self.x_min: float = 0  # Location.Left
        self.y_min: float = 0  # Location.Front
        self.y_max: float = self.y_size  # Location.Back
        self.z_min: float = 0  # Location.Bottom
        self.z_max: float = self.z_size  # Location.Top
        self.bounding_box = {}
        self.rotmax = [self.x_size, self.y_size, self.z_size]
        self.moves = [0, 0, 0]
        self.rotate = [0, 0, 0]
        self.final_location = False

    def make_hole(
        self,
        x: float,
        y: float,
        side: str,
        diameter: float,
        depth: float,
        inner: bool = True,
    ):
        """!!!!!THIS METHOD WILL ONLY WORK IF WE ARE MAKING HOLES IN THE CENTRE OF A CUBIC OBJECT, NEED TO RETHINK LOGIC!!!!!!
        If instead of Location.top and Location.bottom it were possible to think rather (x, y, z_max)
        it would be more affective as the guessing wouldn't need to occur.
        These if statements wouldn't and is would work even when not a square.
        It would however require more lines of code to be written on the user end.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            side: The side of the part the hole will be made in.
            diameter: The diameter of the hole.
            depth: The depth of the hole. If Null the hole is through the part.
            inner: If this is an internal or an external hole.
        """

        location_output = self.side_location_calculator(side=side, x=x, y=y)
        temp_hole = Holes(
            side=side, x=location_output[0], y=location_output[1], z=location_output[2], big=diameter, depth=depth
        )
        if inner:
            self.features.append(temp_hole)
        else:
            self.features.append(temp_hole)
            self.move_holes.append(temp_hole)

    def make_slot(
        self,
        x: float,
        y: float,
        side: str,
        x_size: float,
        y_size: float,
        z_size: float,
        horizontal: bool = True,
        inner=True,
    ):
        """!!!!!THIS METHOD WILL ONLY WORK IF WE ARE MAKING HOLES IN THE CENTRE OF A CUBIC OBJECT, NEED TO RETHINK LOGIC!!!!!!
        If instead of Location.top and Location.bottom it were possible to think rather (x, y, z_max)
        it would be more affective as the guessing wouldn't need to occur.
        These if statements wouldn't and is would work even when not a square.
        It would however require more lines of code to be written on the user end."""

        location_output = self.side_location_calculator(side=side, x=x, y=y)
        temp_slot = Slot(
            side=side,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
            x=location_output[0],
            y=location_output[1],
            z=location_output[2],
            Horizontal=horizontal,
        )
        # This will add it to the relevnt array
        if inner:
            self.features.append(temp_slot)
        else:
            self.features.append(temp_slot)
            self.move_holes.append(temp_slot)

    def make_nut(self, side: str, x: float, y: float, type: float, depth: float, sink: float):
        """This class will be used for cutting nut cut outs into an odject. It still requires
        some developement to improve accuracy."""

        location_output = self.side_location_calculator(side=side, x=x, y=y, sink=sink)
        temp_nut = NutCutOut(
            side=side, x=location_output[0], y=location_output[1], z=location_output[2], type=type, depth=depth
        )
        self.features.append(temp_nut)

    def make_rectangle(
        self,
        side: str,
        x: float,
        y: float,
        height: float,
        width: float,
        depth: float,
        sink=0,
        center=False,
    ):
        """This will cut a block out of the object."""

        location_output = self.side_location_calculator(side=side, x=x, y=y, sink=sink)
        temp_rect = RectangleCutOut(
            side=side,
            width=width,
            x=location_output[0],
            y=location_output[1],
            z=location_output[2],
            height=height,
            depth=depth,
            center=center,
        )
        self.features.append(temp_rect)

    def make_bounding_box(self):
        """This bounding box will be used to help keep track of and update the bounds."""

        self.bounding_box = {
            "TOP": self.z_max,
            "BOTTOM": self.z_min,
            "LEFT": self.x_min,
            "RIGHT": self.x_max,
            "FRONT": self.y_min,
            "BACK": self.y_max,
        }

    def move(self, x=0, y=0, z=0):
        """This method will be used for moving the part."""

        x_size = self.x_max - self.x_min
        y_size = self.y_max - self.y_min
        z_size = self.z_max - self.z_min

        if x != 0:
            self.x_min = x
            self.x_max = x + x_size
            self.moves[0] = x
        if y != 0:
            self.y_min = y
            self.y_max = y + y_size
            self.moves[1] = y
        if z != 0:
            self.z_min = z
            self.z_max = z + z_size
            self.moves[2] = z

        self.make_bounding_box()

    def insert_hole(self, hole):
        """This method will be used for inserting the hole into an object."""

        if self.moves[0] != 0:
            hole.move(x=-self.moves[0])
        if self.moves[1] != 0:
            hole.move(y=-self.moves[1])
        if self.moves[2] != 0:
            hole.move(z=-self.moves[2])

        if self.rotate[0] != 0:
            hole.swap_yz(((360 - self.rotate[0]) / 90), self.rotmax[1])
        if self.rotate[1] != 0:
            hole.swap_xz(((360 - self.rotate[1]) / 90), self.rotmax[2])
        if self.rotate[2] != 0:
            hole.swap_xy(((360 - self.rotate[2]) / 90), self.rotmax[0])

        self.features.append(hole)
        self.move_holes.append(hole)
