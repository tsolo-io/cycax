from location import location
from holes import holes
from rectange_cut_out import rectangle_cut_out
from nut_cut_out import nut_cut_out
from slot import slot

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class part(location):
    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        side: str,
        part_no: str,
        x_size: float,
        y_size: float,
        z_size: float,
    ):
        super().__init__(x, y, z, side)
        self.part_no = part_no
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.features = []  # Stores all the holes to be cut
        self.move_holes = []
        self.x_max: float = self.x_size  # Right
        self.x_min: float = 0  # Left
        self.y_min: float = 0  # Front
        self.y_max: float = self.y_size  # Back
        self.z_min: float = 0  # Bottom
        self.z_max: float = self.z_size  # Top
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
        Inner: bool = True,
    ):
        """!!!!!THIS METHOD WILL ONLY WORK IF WE ARE MAKING HOLES IN THE CENTRE OF A CUBIC OBJECT, NEED TO RETHINK LOGIC!!!!!!
        If instead of top and bottom it were possible to think rather (x, y, z_max) it would be more affective as the guessing wouldn't need to occur. These if statements wouldn't and is would work even when not a square.
        It would however require more lines of code to be written on the user end."""
        if side == TOP:
            temp_hole = holes(side, x, y, self.z_max, diameter, depth)
        if side == BOTTOM:
            temp_hole = holes(side, x, y, self.z_min, diameter, depth)
        if side == LEFT:
            temp_hole = holes(side, self.x_min, x, y, diameter, depth)
        if side == RIGHT:
            temp_hole = holes(side, self.x_max, x, y, diameter, depth)
        if side == FRONT:
            temp_hole = holes(side, x, self.y_min, y, diameter, depth)
        if side == BACK:
            temp_hole = holes(side, x, self.y_max, y, diameter, depth)
        else:
            exit
        # This will add it to the relevnt array
        if Inner:
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
        Inner=True,
    ):
        """!!!!!THIS METHOD WILL ONLY WORK IF WE ARE MAKING HOLES IN THE CENTRE OF A CUBIC OBJECT, NEED TO RETHINK LOGIC!!!!!!
        If instead of top and bottom it were possible to think rather (x, y, z_max) it would be more affective as the guessing wouldn't need to occur. These if statements wouldn't and is would work even when not a square.
        It would however require more lines of code to be written on the user end."""
        if side == TOP:
            temp_slot = slot(
                side=side,
                x_size=x_size,
                y_size=y_size,
                z_size=z_size,
                x=x,
                y=y,
                z=self.z_max,
                Horizontal=horizontal,
            )
        if side == BOTTOM:
            temp_slot = slot(
                side=side,
                x_size=x_size,
                y_size=y_size,
                z_size=z_size,
                x=x,
                y=y,
                z=self.z_min,
                Horizontal=horizontal,
            )
        if side == LEFT:
            temp_slot = slot(
                side=side,
                x_size=x_size,
                y_size=y_size,
                z_size=z_size,
                x=self.x_min,
                y=x,
                z=y,
                Horizontal=horizontal,
            )
        if side == RIGHT:
            temp_slot = slot(
                side=side,
                x_size=x_size,
                y_size=y_size,
                z_size=z_size,
                x=self.x_max,
                y=x,
                z=y,
                Horizontal=horizontal,
            )
        if side == FRONT:
            temp_slot = slot(
                side=side,
                x_size=x_size,
                y_size=y_size,
                z_size=z_size,
                x=x,
                y=self.y_min,
                z=y,
                Horizontal=horizontal,
            )
        if side == BACK:
            temp_slot = slot(
                side=side,
                x_size=x_size,
                y_size=y_size,
                z_size=z_size,
                x=x,
                y=self.y_max,
                z=y,
                Horizontal=horizontal,
            )
        else:
            exit
        # This will add it to the relevnt array
        if Inner:
            self.features.append(temp_slot)
        else:
            self.features.append(temp_slot)
            self.move_holes.append(temp_slot)

    def make_nut(
        self, side: str, x: float, y: float, type: float, depth: float, sink: float
    ):
        """This class will be used for cutting nut cut outs into an odject. It still requires some developement to improve accuracy."""

        if side == TOP:
            temp_nut = nut_cut_out(side, x, y, self.z_max - sink, type, depth)
        if side == BOTTOM:
            temp_nut = nut_cut_out(side, x, y, self.z_min + sink, type, depth)
        if side == LEFT:
            temp_nut = nut_cut_out(side, self.x_min + sink, x, y, type, depth)
        if side == RIGHT:
            temp_nut = nut_cut_out(side, self.x_max - sink, x, y, type, depth)
        if side == FRONT:
            temp_nut = nut_cut_out(side, x, self.y_min + sink, y, type, depth)
        if side == BACK:
            temp_nut = nut_cut_out(side, x, self.y_max - sink, y, type, depth)
        else:
            exit
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

        if side == TOP:
            temp_rect = rectangle_cut_out(
                side, width, x, y, self.z_max - sink, height, depth, center
            )
        if side == BOTTOM:
            temp_rect = rectangle_cut_out(
                side, width, x, y, self.z_min + sink, height, depth, center
            )
        if side == LEFT:
            temp_rect = rectangle_cut_out(
                side, width, self.x_min + sink, x, y, height, depth, center
            )
        if side == RIGHT:
            temp_rect = rectangle_cut_out(
                side, width, self.x_max - sink, x, y, height, depth, center
            )
        if side == FRONT:
            temp_rect = rectangle_cut_out(
                side, width, x, self.y_min + sink, y, height, depth, center
            )
        if side == BACK:
            temp_rect = rectangle_cut_out(
                side, width, x, self.y_max - sink, y, height, depth, center
            )
        else:
            exit
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

    def at(self, X=0, Y=0, Z=0):
        """This method will be used for moving the part."""

        x_size = self.x_max - self.x_min
        y_size = self.y_max - self.y_min
        z_size = self.z_max - self.z_min

        if X != 0:
            self.x_min = X
            self.x_max = X + x_size
            self.moves[0] = X
        if Y != 0:
            self.y_min = Y
            self.y_max = Y + y_size
            self.moves[1] = Y
        if Z != 0:
            self.z_min = Z
            self.z_max = Z + z_size
            self.moves[2] = Z

        self.make_bounding_box()

    def insert_hole(self, hole):
        """This method will be used for inserting the hole into an object."""

        if self.moves[0] != 0:
            hole.at(x=-self.moves[0])
        if self.moves[1] != 0:
            hole.at(y=-self.moves[1])
        if self.moves[2] != 0:
            hole.at(z=-self.moves[2])

        if self.rotate[0] != 0:
            hole.swapYZ(((360 - self.rotate[0]) / 90), self.rotmax[1])
        if self.rotate[1] != 0:
            hole.swapXZ(((360 - self.rotate[1]) / 90), self.rotmax[2])
        if self.rotate[2] != 0:
            hole.swapXY(((360 - self.rotate[2]) / 90), self.rotmax[0])

        self.features.append(hole)
        self.move_holes.append(hole)
