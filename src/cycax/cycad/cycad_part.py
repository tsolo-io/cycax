import copy
import json
import logging
from pathlib import Path

from cycax.cycad.beveled_edge import BeveledEdge
from cycax.cycad.cycad_side import BackSide, BottomSide, CycadSide, FrontSide, LeftSide, RightSide, TopSide
from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from cycax.cycad.engines.part_openscad import PartEngineOpenSCAD
from cycax.cycad.engines.simple_2d import Simple2D
from cycax.cycad.features import Holes, NutCutOut, RectangleCutOut, SphereCutOut
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP, Location
from cycax.cycad.slot import Slot


class CycadPart(Location):
    """Define a Part in CyCAd.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        x_size: The size along the x axis.
        y_size: The size along the y axis.
        z_size: The size along the z axis.
        part_no : The unique name that will be given to a type of parts.
        polygon: currently only cube available.
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
        polygon: str,
        colour: str = "orange",
        assembly=None,
    ):
        super().__init__(x, y, z, side)
        self._name: str = ""
        self.left = LeftSide(self)
        self.right = RightSide(self)
        self.top = TopSide(self)
        self.bottom = BottomSide(self)
        self.front = FrontSide(self)
        self.back = BackSide(self)

        self._base_path = Path(".")
        self.part_no = part_no.strip().replace("-", "_").lower()
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
        self.position = [0, 0, 0]
        self.rotation = []
        self.final_location = False
        self.polygon = polygon
        self.colour = colour
        self.labels: set[str] = set()
        self._files = {}
        self.definition()
        self.assembly = assembly

    def definition(self):
        """This method will be ovedridden to do a calculation."""
        pass

    def add_file(self, file_type: str, file_path: Path):
        """
        This method will use the 3D model provided in the path rather than the object drawn.

        Args:
            file_type: The file type.
            file_path: The path to the file.
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
        *,
        external_subtract: bool = False,
    ):
        """
        If instead of Location.top and Location.bottom it were possible to think rather (x, y, z_max)
        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            diameter: The diameter of the hole.
            depth: The depth of the hole. If Null the hole is through the part.
            external_subtract: This is to specify that the hole should only be cut into other surfaces and not itself.
        """

        temp_hole = Holes(side=side, x=x, y=y, z=z, diameter=diameter, depth=depth)
        if external_subtract:
            self.move_holes.append(temp_hole)
        else:
            self.features.append(temp_hole)

    def make_slot(
        self,
        x: float,
        y: float,
        z: float,
        side: str,
        x_size: float,
        y_size: float,
        z_size: float,
        *,
        horizontal: bool = True,
        external_subtract: bool = False,
    ):
        """This method will insert a slot into a CycadPart.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            x_size : The size of x of slot.
            y_size : The size of y of slot.
            z_size : The size of z of slot.
            horizontal : This can be overridden if it is preferred to have a vertical slot.
            external_subtract: This is to specify that the slot should only be cut into other surfaces and not itself.
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
        # This will add it to the relevant array
        if external_subtract:
            self.move_holes.append(temp_slot.hole_left)
            self.move_holes.append(temp_slot.hole_right)
            self.move_holes.append(temp_slot.rectangle)
        else:
            self.features.append(temp_slot.hole_left)
            self.features.append(temp_slot.hole_right)
            self.features.append(temp_slot.rectangle)

    def make_nut(
        self,
        side: str,
        x: float,
        y: float,
        z: float,
        nut_type: str,
        depth: float | None = None,
        *,
        vertical: bool = True,
    ):
        """This method will insert a nut into a CycadPart.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            nut_type: This is the type of nut specified as a float. This method will be updated in version 2.
            depth: This is how deep the nut cut out must be.
            vertical: This will be set to False if you want the flat side rather than the pointy side down.
        """
        temp_nut = NutCutOut(side=side, x=x, y=y, z=z, nut_type=nut_type, depth=depth, vertical=vertical)
        self.features.append(temp_nut)

    def make_sphere(self, side: str, x: float, y: float, z: float, diameter: float):
        """This method will insert a sphere into a CycadPart.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            diameter: The Diameter of the sphere.
        """
        temp_sphere = SphereCutOut(side=side, x=x, y=y, z=z, diameter=diameter)
        self.features.append(temp_sphere)

    def make_rectangle(
        self,
        side: str,
        x: float,
        y: float,
        z: float,
        x_size: float,
        y_size: float,
        z_size: float,
        *,
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
            center : This can be overridden if you would like object centered at origin.
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

    def move(self, x: float | None = None, y: float | None = None, z: float | None = None):
        """This method will be used for moving the part.

        Args:
            x: the amount the object should be moved by along the x axis.
            y: the amount the object should be moved by along the y axis.
            z: the amount the object should be moved by along the z axis


        """

        x_size = self.x_max - self.x_min
        y_size = self.y_max - self.y_min
        z_size = self.z_max - self.z_min

        if x is not None:
            self.x_min = self.x_min + x
            self.x_max = self.x_min + x_size
            self.position[0] = self.position[0] + x
        if y is not None:
            self.y_min = self.y_min + y
            self.y_max = self.y_min + y_size
            self.position[1] = self.position[1] + y
        if z is not None:
            self.z_min = self.z_min + z
            self.z_max = self.z_min + z_size
            self.position[2] = self.position[2] + z

        self.make_bounding_box()

    def at(self, x: float | None = None, y: float | None = None, z: float | None = None):
        """Place part at the exact provided coordinates.

        Args:
            x: The value to which x needs to be moved to on the axis.
            y: The value to which y needs to be moved to on the axis.
            z: The value to which z needs to be moved to on the axis.
        """
        x_size = self.x_max - self.x_min
        y_size = self.y_max - self.y_min
        z_size = self.z_max - self.z_min

        if x is not None:
            self.x_min = x
            self.x_max = x + x_size
            self.position[0] = x
        if y is not None:
            self.y_min = y
            self.y_max = y + y_size
            self.position[1] = y
        if z is not None:
            self.z_min = z
            self.z_max = z + z_size
            self.position[2] = z

    def insert_hole(self, hole: Holes):
        """This method will be used for inserting the hole into an object.

        Args:
            hole: hole to be inserted.


        """

        if self.position[0] != 0:
            hole.move(x=-self.position[0])
        if self.position[1] != 0:
            hole.move(y=-self.position[1])
        if self.position[2] != 0:
            hole.move(z=-self.position[2])

        working_rotate = copy.deepcopy(self.rotation)
        rotation = [self.x_max - self.x_min, self.y_max - self.y_min, self.z_max - self.z_min]
        while len(working_rotate) > 0:
            rot = working_rotate.pop()
            if rot["axis"] == "x":
                rotation = hole.swap_yz(3, rotation)
            if rot["axis"] == "y":
                rotation = hole.swap_xz(3, rotation)
            if rot["axis"] == "z":
                rotation = hole.swap_xy(3, rotation)
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
        This takes the provided part and will create its dictionary and export it to a JSON

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

    def export(self) -> dict:
        """
        This method will take the values stored within the part and export it to a dict so that it can be decoded.

        Returns:
            dict : The dictionary of the part.
        """

        dict_piece = {
            "name": self.polygon,
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
            list_part.append(ret)
        dict_out = {}
        dict_out["name"] = self.part_no
        dict_out["features"] = list_part
        return dict_out

    def beveled_edge(self, edge_type: str, side1: str, side2: str, size: float):
        """This method will shape a edge of a CycadPart.

        Args:
            edge_type: round or chamfer.
            side1: side on edge.
            side2: side on edge.
            size: The radius of a round when rounding or the length of a chamfer.
        """
        edge = []
        self.make_bounding_box()
        for side in [side1, side2]:
            edge.append(
                {
                    TOP: "z",
                    BACK: "y",
                    BOTTOM: "z",
                    FRONT: "y",
                    LEFT: "x",
                    RIGHT: "x",
                }[side]
            )
        assert edge[0] != edge[1], f"Cannot use {side1} and {side2}"
        assert edge_type in ["round", "chamfer"], "You need to specify the edge type as either round or chamfer."
        if "x" not in edge:
            side = "LEFT"
            depth = self.bounding_box["RIGHT"]
        elif "y" not in edge:
            side = "FRONT"
            depth = self.bounding_box["BACK"]
        elif "z" not in edge:
            side = "BOTTOM"
            depth = self.bounding_box["TOP"]
        self.features.append(
            BeveledEdge(
                edge_type=edge_type,
                axis1=edge[0],
                bound1=self.bounding_box[side1],
                axis2=edge[1],
                bound2=self.bounding_box[side2],
                size=size,
                side=side,
                depth=depth,
            )
        )

    def render(self, engine: str = "Preview3D", engine_config: dict | None = None) -> dict:
        """This class will render the necessary diagrams when called with the following methods.
        It is invoked by CycadPart and can be called: CycadPart.render(engine="simple2D", engine_config={"side": "left"}).

        Args:
            engine: Name of the engine to use.
            engine_config: Configuration passed on to the PartEngine. It is engine specific.
        """

        _eng_lower = engine.lower()
        if _eng_lower == "simple2d":
            part_engine = Simple2D(name=self.part_no, path=self._base_path, config=engine_config)

        elif _eng_lower == "openscad":
            if not engine_config:
                engine_config = {"stl": True}
            part_engine = PartEngineOpenSCAD(name=self.part_no, path=self._base_path, config=engine_config)

        elif _eng_lower == "preview3d":
            part_engine = PartEngineOpenSCAD(name=self.part_no, path=self._base_path, config={"stl": False})

        elif _eng_lower == "freecad":
            if engine_config is None:
                engine_config = {}
                engine_config["out_formats"] = [("png", "ALL"), ("STL",), ("DXF", TOP)]
            part_engine = PartEngineFreeCAD(name=self.part_no, path=self._base_path, config=engine_config)

        else:
            msg = f"engine: {engine} is not one of Simple2D, OpenSCAD, Preview3D or FreeCAD."
            raise ValueError(msg)

        return self.build(part_engine)

    def build(self, engine: PartEngine) -> list:
        """Build the part with the given PartEngine.

        Args:
            engine: The instance of PartEngine to use.

        Returns:
            The list of files created when the PartEngine was called.
        """
        return engine.build()

    def get_name(self, default: str = None):
        """Return the part name, if the part has not been named generate a name.

        The part name (or ID) is distict from the part_no or part number.
        Each instance of the part has a unique name, but is still the same type of part as the
        parts with the same part number.
        Parts could override this method to define a specialised part numbering scheme.

        Args:
            default: A possible name for this part if the part has not been named.
                And if it is not being used by another part.
        """

        if not self._name:
            # I am name-less.
            used_names = self.assembly.parts.keys()
            if default and default not in used_names:
                # Check if we have a default name and that it has not been used.
                self._name = default

            else:
                sequence_n = 0

                while True:
                    sequence_n += 1
                    suggested_name = f"{self.part_no}_{sequence_n}"
                    if suggested_name not in used_names:
                        self._name = suggested_name
                        break

        return self._name

    def get_side(self, side_name: str) -> CycadSide:
        return getattr(self, side_name.lower())

    def level(
        self,
        *,
        left: LeftSide = None,
        right: RightSide = None,
        front: FrontSide = None,
        back: BackSide = None,
        top: TopSide = None,
        bottom: BottomSide = None,
        subtract: bool = False,
    ):
        """
        A short hand level method for part.

        This method can only be used if the CycaxPart was added to an Assembly.
        The method to replace multiple calls to assembly.level and assembly.subtract for a part.

        Args:
            left: Side to lign the left side up with.
            right: Side to lign the right side up with
            front: Side to lign the front up with.
            back: Side to lign the back up with.
            top: Side to lign the top up with.
            bottom: Side to lign the bottom up with
            subtract: if subtrace is set to True
                it will transfer the holes from one part to the other.

        Raises:
            ValueError: When both left and right side is give.
            ValueError: When both front and back side is give.
            ValueError: When both top and bottom side is give.
        """
        assert self.assembly, "The assembly has not been specified for this cycad part."

        level_tasks = []
        if left is not None:
            if right is not None:
                msg = " "
                raise ValueError(msg)
            level_tasks.append((self.left, left))
        elif right is not None:
            level_tasks.append((self.right, right))

        if top is not None:
            if bottom is not None:
                msg = " "
                raise ValueError(msg)
            level_tasks.append((self.top, top))
        elif bottom is not None:
            level_tasks.append((self.bottom, bottom))

        if front is not None:
            if back is not None:
                msg = " "
                raise ValueError(msg)
            level_tasks.append((self.front, front))
        elif back is not None:
            level_tasks.append((self.back, back))

        for my_side, other_side in level_tasks:
            self.assembly.level(my_side, other_side)

        if subtract:
            for my_side, other_side in level_tasks:
                self.assembly.subtract(other_side, self)

    def rotate(self, actions: str):
        """
        This can be used to rotate a part in the assembly as follows:
        CycadPart.rotate("xxyzyy")
        This is: 2 rotate_freeze_front, rotate_freeze_left, rotate_freeze_top, 2 rotate_freeze_left.
        Where rotate_freeze_ results in one 90degrees counter clock wise rotations around the specified axis.
        Args:
            actions: This is a string specifying rotations.

        Raises:
            ValueError: When the given actions contains a string that is non x, y, or z.
        """
        for action in actions:
            match action.lower():
                case "x":
                    self.assembly.rotate_freeze_left(self)
                case "y":
                    self.assembly.rotate_freeze_front(self)
                case "z":
                    self.assembly.rotate_freeze_top(self)
                case _:
                    msg = f"""The actions permissable by rotate are 'x', 'y' or 'z'.
                            {action} is not one of the permissable actions."""
                    raise ValueError(msg)
