import json
import logging
import os
from pathlib import Path

from cycax.cycad.cycad_side import BackSide, BottomSide, FrontSide, LeftSide, RightSide, TopSide
from cycax.cycad.engine_openscad import EngineOpenSCAD
from cycax.cycad.features import Holes, NutCutOut, RectangleCutOut
from cycax.cycad.figure import Figure
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP, Location
from cycax.cycad.slot import Slot


class CycadPart(Location):
    """This will be the class that specifies certain details with regards to the CycadPart.
    This class will initialize a CycadPart at the desired location.

    Args:
        x : The location of x along the x axis.
        y : The location of y along the y axis.
        z : The location of z along the z axis.
        x_size : The size of x.
        y_size : The size of y.
        z_size : The siez of z.
        part_no : The unique name that will be given to a type of parts.
        poligon: currently only cube availabe.
        colour: colour of the part.

    """

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
        poligon: str,
        colour: str = "orange",
    ):
        super().__init__(x, y, z, side)
        self.left = LeftSide(self)
        self.right = RightSide(self)
        self.top = TopSide(self)
        self.bottom = BottomSide(self)
        self.front = FrontSide(self)
        self.back = BackSide(self)

        self._base_path = Path(".")
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
        self.poligon = poligon
        self.colour = colour
        self.label: set[str] = set()
        self._files = {}
        self.definition()

    def definition(self):
        """This method will be ovedridden to do a calculation."""
        pass

    def add_file(self, file_type: str, file_path: Path):
        """
        This method will use the 3D model provided in the path rather than the object drawn.

        Args:
            file_type: this is the extenstion name of the file.
            file_path: this is the path to the file.
        """
        f_type = str(file_type).upper().strip()
        self._files[f_type] = file_path
        if not file_path.exists():
            logging.warning("File does not exists. Its ok we carry on but its not good.")
        self.colour = "purple"
        self.name = "external"
        self.x, self.y, self.z = self.x_size / 2, self.y_size / 2, self.z_size / 2

    def add_labels(self, label_names: str):
        """This method adds a label:
        Args:
            label_names: add these labels.
        """
        for label in label_names:
            self.labels.add(str(label).lower())

    def make_hole(
        self,
        x: float,
        y: float,
        z: float,
        side: str,
        diameter: float,
        depth: float,
        inner: bool = True,
        external_only: bool = False,
    ):
        """!!!!!THIS METHOD WILL ONLY WORK IF WE ARE MAKING HOLES IN THE CENTRE OF A CUBIC OBJECT, NEED TO RETHINK LOGIC!!!!!!
        If instead of Location.top and Location.bottom it were possible to think rather (x, y, z_max)
        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            diameter: The diameter of the hole.
            depth: The depth of the hole. If Null the hole is through the part.
            inner: If this is an internal or an external hole.
        """

        temp_hole = Holes(side=side, x=x, y=y, z=z, diameter=diameter, depth=depth)
        if external_only:
            self.move_holes.append(temp_hole)
        elif inner:
            self.features.append(temp_hole)
        elif not inner:
            self.features.append(temp_hole)
            self.move_holes.append(temp_hole)

    def make_slot(
        self,
        x: float,
        y: float,
        z: float,
        side: str,
        x_size: float,
        y_size: float,
        z_size: float,
        horizontal: bool = True,
        inner: bool = True,
        external_only: bool = False,
    ):
        """This method will insert a slot into a CycadPart.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            x_size : The size of x of slot.
            y_size : The size of y of slot.
            z_size : The siez of z of slot.
            horizontal : This can be overridden if it is preferred to have a verticle slot.
            inner: If this is an internal or an external hole.
        """

        temp_slot = Slot(
            side=side,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
            x=x,
            y=y,
            z=z,
            horizontal=horizontal,
        )
        # This will add it to the relevnt array
        if external_only:
            self.move_holes.append(temp_slot.hole_left)
            self.move_holes.append(temp_slot.hole_right)
            self.move_holes.append(temp_slot.rectangle)
        elif inner:
            self.features.append(temp_slot.hole_left)
            self.features.append(temp_slot.hole_right)
            self.features.append(temp_slot.rectangle)
        elif not inner:
            self.move_holes.append(temp_slot.hole_left)
            self.move_holes.append(temp_slot.hole_right)
            self.move_holes.append(temp_slot.rectangle)
            self.features.append(temp_slot.hole_left)
            self.features.append(temp_slot.hole_right)
            self.features.append(temp_slot.rectangle)

    def make_nut(self, side: str, x: float, y: float, z: float, nut_type: float, depth: float):
        """This method will insert a nut into a CycadPart.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            nut_type: This is the type of nut specified as a float. This method will be updated in version 2.
            depth: This is how deep the nut cut out must be.
        """
        temp_nut = NutCutOut(side=side, x=x, y=y, z=z, nut_type=nut_type, depth=depth)
        self.features.append(temp_nut)

    def make_rectangle(
        self,
        side: str,
        x: float,
        y: float,
        z: float,
        x_size: float,
        y_size: float,
        z_size: float,
        center=False,
    ):
        """This method will cut a block out of the CycadPart.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            x_size : The size of x of rectangle.
            y_size : The size of y of rectangle.
            z_size : The size of z of rectangle.
            center : This can be overridden if you would like to have the location of the cut out specified from its center.
        """

        temp_rect = RectangleCutOut(
            side=side,
            x=x,
            y=y,
            z=z,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
            center=center,
        )
        self.features.append(temp_rect)

    def make_bounding_box(self):
        """This bounding box will be used to help keep track of and update the bounds.
        This method is used extensively in assemble to keep track of where the box "should" be after moving it around.
        """

        self.bounding_box = {
            "TOP": self.z_max,
            "BOTTOM": self.z_min,
            "LEFT": self.x_min,
            "RIGHT": self.x_max,
            "FRONT": self.y_min,
            "BACK": self.y_max,
        }

    def move(self, x: float = None, y: float = None, z: float = None):
        """This method will be used for moving the part.

        Args:
            x: the amount the object should be moved along the x axis.
            y: the amount the object should be moved along the y axis.
            z: the amound the object should be moved along the z axis


        """

        x_size = self.x_max - self.x_min
        y_size = self.y_max - self.y_min
        z_size = self.z_max - self.z_min

        if x is not None:
            self.x_min = x
            self.x_max = x + x_size
            self.moves[0] = x
        if y is not None:
            self.y_min = y
            self.y_max = y + y_size
            self.moves[1] = y
        if z is not None:
            self.z_min = z
            self.z_max = z + z_size
            self.moves[2] = z

        self.make_bounding_box()

    def insert_hole(self, hole: Holes):
        """This method will be used for inserting the hole into an object.

        Args:
            hole: hole to be inserted.


        """

        if self.moves[0] != 0:
            hole.move(x=-self.moves[0])
        if self.moves[1] != 0:
            hole.move(y=-self.moves[1])
        if self.moves[2] != 0:
            hole.move(z=-self.moves[2])

        rotation = [self.x_size, self.y_size, self.z_size]
        if self.rotate[0] != 0:
            rotation = hole.swap_yz(((360 - self.rotate[0]) / 90), rotation)
        if self.rotate[1] != 0:
            rotation = hole.swap_xz(((360 - self.rotate[1]) / 90), rotation)
        if self.rotate[2] != 0:
            rotation = hole.swap_xy(((360 - self.rotate[2]) / 90), rotation)
        if hole.side == TOP or hole.side == BOTTOM:
            hole.depth = self.z_size
        if hole.side == LEFT or hole.side == RIGHT:
            hole.depth = self.x_size
        if hole.side == FRONT or hole.side == BACK:
            hole.depth = self.y_size
        self.features.append(hole)
        self.move_holes.append(hole)

    def save(self, path: Path | None = None):
        """
        This takes the provided part and will create its dictionary and export it to a json
        Args:
            path: Base path for storing part information.
                  A directory with the part_no will be created in this path.
        """
        if path is None:
            path = Path(".")
        if not path.exists():
            msg = f"The directory {path} does not exists."
            raise FileNotFoundError(msg)

        self._base_path = path
        dir_name = path / self.part_no
        dir_name.mkdir(exist_ok=True)
        file_path = dir_name / f"{self.part_no}.json"
        json.dump(self.export(), file_path.open("w+"))

    def export(self) -> list:
        """
        This method will take the values stored within the part and export it to a dict so that it can be decoded.

        Returns:
            list : The dictionary of the part.
        """

        dict_piece = {
            "name": self.poligon,
            "type": "add",
            "side": self.side,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "x_size": self.x_size,
            "y_size": self.y_size,
            "z_size": self.z_size,
            "center": False,
        }

        list_part = []

        list_part.append(dict_piece)
        for item in self.features:
            ret = item.export()
            if type(ret) != dict:
                for part in ret:
                    list_part.append(part)
            else:
                list_part.append(ret)
        return list_part

    def render(self, eng: str, side: str = None):
        """This class will render the necessary diagrams when called with the following methods. It is invoked int CycadPart and can be called: CycadPart.render.pyplot(left).
        Args:
            eng: type of engine to use
            side: this will be used for pyplot
        """

        if eng == "simple2D":
            # This method will created a pyplot drawing of the object.
            if side is None:
                side = "TOP"
            plotter = Figure(part_no=self.part_no, side=side)
            plotter.save_as_figure()

        elif eng == "OpenSCAD":
            # This method will produce an OpenSCAD 3D drawing of the given object.
            cutter = EngineOpenSCAD()

            in_name = "{cwd}/{data}/{data}.json".format(cwd=self._base_path, data=self.part_no)

            if not os.path.exists(in_name):
                self.save()

            cutter.decode(self.part_no)

        elif eng == "STL":
            # This method will convert a OpenSCAD drawing of a given file into a STL drawing.
            cutter = EngineOpenSCAD()
            in_name = "{cwd}/{data}/{data}.scad".format(cwd=self._base_path, data=self.part_no)

            if not os.path.exists(in_name):
                self.Render("OpenSCAD")

            cutter.render_stl(self)

        else:
            msg = f"engine: {eng} is not one of simple2D, OpenSCAD or STL."
            raise ValueError(msg)
