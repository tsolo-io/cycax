# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from turtle import position
from typing import TYPE_CHECKING, Self

from cycax.cycad.beveled_edge import BeveledEdge
from cycax.cycad.cycad_side import BackSide, BottomSide, CycadSide, FrontSide, LeftSide, RightSide, TopSide
from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from cycax.cycad.engines.part_openscad import PartEngineOpenSCAD
from cycax.cycad.engines.simple_2d import Simple2D
from cycax.cycad.features import Feature, Holes, NutCutOut, RectangleCutOut, SphereCutOut
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP, Location
from cycax.cycad.slot import Slot

if TYPE_CHECKING:
    from cycax.cycad.assembly import Assembly


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
        assembly: The assembly this part is a component of.

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
        assembly: Assembly | None = None,
    ):
        super().__init__(x, y, z, side)
        self._name: str = ""
        self.left = LeftSide(self)
        self.right = RightSide(self)
        self.top = TopSide(self)
        self.bottom = BottomSide(self)
        self.front = FrontSide(self)
        self.back = BackSide(self)

        self._base_path = None
        self.part_no = part_no.strip().replace("-", "_").lower()
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.features = []  # Stores all the holes to be cut
        self.move_holes = []
        self.x_min: float = 0.0  # Location.Left
        self.y_min: float = 0.0  # Location.Front
        self.z_min: float = 0.0  # Location.Bottom
        self.x_max: float = self.x_size  # Location.Right
        self.y_max: float = self.y_size  # Location.Back
        self.z_max: float = self.z_size  # Location.Top
        self.bounding_box = {}
        self.position = [0.0, 0.0, 0.0]  
        self.rotation = []
        self.final_location = False
        self.initial_polygon = polygon
        self.colour = colour
        self.labels: set[str] = set()
        self._files = {}
        self.definition()
        self.assembly = assembly
        if assembly:
            assembly.add(self)
            # Assembly will set: part._base_path == assembly._base_path

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

    def make_countersinc(self, side: str, diameter: float, angle: float = 90):
        """Countersinc all holes on the side.

        This includes holes drilled from this and opposite side.

        """
        # A Counter drill with no bole.
        self.make_counterdrill(side=side, diameter=diameter, depth=0, angle=angle)

    def make_counterbore(self, side: str, diameter: float, depth: float):
        """Counterbore all holes on the side.

        This includes holes drilled from this and opposite side.

        """
        side_obj = self.get_side(side)
        new_holes = []
        for feature in self.features:
            if feature.name not in ("hole",):
                continue
            if feature.side == side:
                _hole = Holes(side=feature.side, x=feature.x, y=feature.y, z=feature.z, diameter=diameter, depth=depth)
                new_holes.append(_hole)
            elif feature.side == side_obj.opposite.name:
                if side == BOTTOM:
                    z = depth
                else:
                    z = self.z_size - depth
                _hole = Holes(side=feature.side, x=feature.x, y=feature.y, z=z, diameter=diameter, depth=depth)
                new_holes.append(_hole)
        self.features.extend(new_holes)

    def make_counterdrill(self, side: str, diameter: float, depth: float, angle: float = 90):
        """Counter drill is a combination of counterbore and countersinc.

        A counterbore hole that was countersunc.
        """

        # TODO: Require cone shape cut.
        msg = "The adding of counterdrill to a side has not been implemented."
        raise NotImplementedError(msg)

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
        external_subtract: bool = False,
        calculate: bool = False,
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
            external_subtract: This feature will be cut from other parts.
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
        if calculate or external_subtract:
            temp_rect.__calc__()
        if external_subtract:
            self.move_holes.append(temp_rect)
        else:
            self.features.append(temp_rect)

    def make_bounding_box(self):
        """This bounding box will be used to help keep track of and update the bounds.
        This method is used extensively in assembly to keep track of where the box "should" be after moving it around.
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

    def insert_feature(self, feature: Feature):
        """This method will be used for inserting the hole into an object.

        Args:
            feature: The feature transferred from the leveled part.
        """
        # TODO: Maybe rename to subtract_feature.
        # NOTE: Issues exist when subtracting rectangles from back of part.
        if self.position[0] != 0.0:
            feature.move(x=-self.position[0])
        if self.position[1] != 0.0:
            feature.move(y=-self.position[1])
        if self.position[2] != 0.0:
            feature.move(z=-self.position[2])

        working_rotate = copy.deepcopy(self.rotation)
        rotation = [self.x_max - self.x_min, self.y_max - self.y_min, self.z_max - self.z_min]
        while len(working_rotate) > 0:
            rot = working_rotate.pop()
            if rot["axis"] == "x":
                rotation = feature.swap_yz(3, rotation)
            elif rot["axis"] == "y":
                rotation = feature.swap_xz(3, rotation)
            elif rot["axis"] == "z":
                rotation = feature.swap_xy(3, rotation)
        if feature.name == "cube":
            if feature.side == TOP:
                feature.z = feature.z - feature.z_size / 2 - self.z_size / 2
                feature.z_size = self.z_size
            elif feature.side == BOTTOM:
                feature.z = feature.z + feature.z_size / 2 + self.z_size / 2
                feature.z_size = self.z_size
            elif feature.side == LEFT:
                feature.x = feature.x + feature.x_size / 2 + self.x_size / 2
                feature.x_size = self.x_size
            elif feature.side == RIGHT:
                feature.x = feature.x - feature.x_size / 2 - self.x_size / 2
                feature.x_size = self.x_size
            elif feature.side == FRONT:
                feature.x = feature.y + feature.y_size / 2 + self.y_size / 2
                feature.x_size = self.y_size
            elif feature.side == BACK:
                feature.x = feature.y - feature.y_size / 2 - self.y_size / 2
                feature.x_size = self.y_size
        elif feature.side in (TOP, BOTTOM):
            feature.depth = self.z_size
        elif feature.side in (LEFT, RIGHT):
            feature.depth = self.x_size
        elif feature.side in (FRONT, BACK):
            feature.depth = self.y_size
        self.features.append(feature)

    @property
    def path(self):
        if self._base_path is None:
            msg = "BasePath has not been defined."
            raise ValueError(msg)
        if not self._base_path.exists():
            msg = "BasePath does not exists."
            raise ValueError(msg)
        return self._base_path / self.part_no
    
    @property
    def center(self) -> list:
        """Return the center of a part."""
        centered_x = self.position[0] + self.x_max/2
        centered_y = self.position[1] + self.y_max/2
        centered_z = self.position[2] + self.z_max/2
        return [centered_x, centered_y, centered_z]
 
    def save(self, path: Path | str | None = None):
        """
        Save the part specification to a JSON file.

        Args:
            path: Base path for storing part information.
                A directory with the part_no will be created in this path.
        """
        if path is None:
            if self._base_path is None:
                # If no path is given and we do not have a path set then use the local directory.
                path = Path(".")
            else:
                path = self._base_path
        else:
            path = Path(path)
            if not path.exists():
                path.mkdir(parents=False, exist_ok=True)
        self._base_path = path

        dir_name = self.path
        dir_name.mkdir(exist_ok=True)
        file_path = dir_name / f"{self.part_no}.json"
        file_path.write_text(json.dumps(self.export()))

    def export(self) -> dict:
        """
        A static representation of the Part, suitable to be saved as JSON.

        The export contains:
            name: The part number.
            features: A list of features. Each feature is a dictionary with a type and feature specific specifications.

        Returns:
            Static representation of the part.
        """

        dict_out = {}
        dict_out["name"] = self.part_no
        dict_out["features"] = [
            {
                "name": self.initial_polygon,
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
        ]
        for item in self.features:
            dict_out["features"].append(item.export())
        dict_out["subtract"] = []
        for item in self.move_holes:
            dict_out["subtract"].append(item.export())
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
        for side in (side1, side2):
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
        if not edge:
            msg = "No edge defined"
            raise ValueError(msg)
        if len(edge) != 2:  # noqa: PLR2004 use of constant
            msg = "Only two edges are allowed"
            raise ValueError(msg)
        if edge[0] == edge[1]:
            msg = "Cannot use the same edge"
            raise ValueError(msg)
        supported_edge_types = ("round", "chamfer")
        if edge_type not in supported_edge_types:
            msg = f"You need to specify the edge type as one of {supported_edge_types}."
            raise ValueError(msg)
        if "x" not in edge:
            side = LEFT
            depth = self.bounding_box[RIGHT]
        elif "y" not in edge:
            side = FRONT
            depth = self.bounding_box[BACK]
        elif "z" not in edge:
            side = BOTTOM
            depth = self.bounding_box[TOP]
        else:
            msg = "Invalid edge definition should be x, y, or z."
            raise ValueError(msg)
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

        It is invoked by CycadPart and can be called:
        CycadPart.render(engine="simple2D", engine_config={"side": "left"}).

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

    def create(self, engine: PartEngine) -> list:
        """Create the part in the given PartEngine.

        Args:
            engine: The instance of PartEngine to use.

        Returns:
            The list of files created when the PartEngine was called.
        """
        return engine.create(self)

    def build(self, engine: PartEngine) -> list:
        """Build the part with the given PartEngine.

        The same as calling engine.build(part).

        Args:
            engine: The instance of PartEngine to use.

        Returns:
            The list of files created when the PartEngine was called.
        """
        return engine.build(self)

    def get_name(self, default: str | None = None):
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

    def _assembly_level(self, my_side: CycadSide, other_side: CycadSide, *, subtract: bool = False) -> CycadPart:
        if self.assembly is None:
            msg = "Part is not part of an assembly. Please add it to an assembly before using this method."
            raise ValueError(msg)
        self.assembly.level(my_side, other_side)
        if subtract:
            self.assembly.subtract(other_side, self)
        return other_side._parent

    def level(
        self,
        *,
        left: CycadSide | None = None,
        right: CycadSide | None = None,
        front: CycadSide | None = None,
        back: CycadSide | None = None,
        top: CycadSide | None = None,
        bottom: CycadSide | None = None,
        subtract: bool = False,
    ):
        """
        A shorthand level method for part.

        This method can only be used if the CycaxPart was added to an Assembly.
        The method is to replace multiple calls to assembly.level and assembly.subtract for a part.

        Args:
            left: Side to lign the left side up with.
            right: Side to lign the right side up with
            front: Side to lign the front up with.
            back: Side to lign the back up with.
            top: Side to lign the top up with.
            bottom: Side to lign the bottom up with
            subtract: When True transfer the features marked as external_subtract from one part to the other,
                      for leveled sides.

        Raises:
            ValueError: When both left and right side is give.
            ValueError: When both front and back side is give.
            ValueError: When both top and bottom side is give.
            ValueError: When the part is not part of an assembly.
            ValueError: When leveling with the same part twice and subtracting.
        """
        level_with = {}
        if left is not None:
            if right is not None:
                msg = "Cannot level left and right at the same time."
                raise ValueError(msg)
            level_with["left"] = left
        elif right is not None:
            level_with["right"] = right

        if top is not None:
            if bottom is not None:
                msg = "Cannot level top and bottom at the same time."
                raise ValueError(msg)
            level_with["top"] = top
        elif bottom is not None:
            level_with["bottom"] = bottom

        if front is not None:
            if back is not None:
                msg = "Cannot level front and back at the same time."
                raise ValueError(msg)
            level_with["front"] = front
        elif back is not None:
            level_with["back"] = back

        parts = []
        for name, var in level_with.items():
            part = self._assembly_level(getattr(self, name), var, subtract=subtract)
            if subtract:
                if part in parts:
                    msg = f"Cannot subtract from the same part twice: {part}"
                    raise ValueError(msg)
                parts.append(part)

    def rotate(self, actions: str):
        """Rotate the part several times.

        Example: `CycadPart.rotate("xxyzyy")` is the same as two `rotate_freeze_front`, `rotate_freeze_left`,
        `rotate_freeze_top`, and two `rotate_freeze_left`.
        Where rotate_freeze_<side> results in one 90degrees counter clock wise rotations on the side.

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
