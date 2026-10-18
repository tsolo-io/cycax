# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import copy
import json
import logging
import warnings
from collections import namedtuple
from pathlib import Path
from typing import TYPE_CHECKING

from cycax.cycad import placement
from cycax.cycad.beveled_edge import BeveledEdge
from cycax.cycad.colour import to_rgb
from cycax.cycad.cycad_side import BackSide, BottomSide, CycadSide, FrontSide, LeftSide, RightSide, TopSide
from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.part_freecad import PartEngineFreeCAD
from cycax.cycad.engines.part_openscad import PartEngineOpenSCAD
from cycax.cycad.features import (
    SHAPE_TYPE_MAP,
    Cylinder,
    Feature,
    Holes,
    NutCutOut,
    RectangleAddOn,
    RectangleCutOut,
    Sphere,
)
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP, Location
from cycax.cycad.slot import Slot
from cycax.spec import SPEC_VERSION, validate_spec

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
        colour: colour of the part (a name or RGB). None = the colour of the material, else
            `default_colour`.
        assembly: The assembly this part is a component of.
        material: The material (cycax.materials.Material); it goes into the spec meta.

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
        colour: str | None = None,
        hash: str = "",  # noqa: A002 Shadows builtin, kept for backwards compatibility
        assembly: Assembly | None = None,
        material=None,
        default_colour: str = "orange",
        manufacture=None,
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
        self.part_no = part_no.strip().replace("-", "_").lower().replace(" ", "_")
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.features = []  # Stores all the holes to be cut
        self.external_features = []
        self.x_min: float = 0.0  # Location.Left
        self.y_min: float = 0.0  # Location.Front
        self.z_min: float = 0.0  # Location.Bottom
        self.x_max: float = self.x_size  # Location.Right
        self.y_max: float = self.y_size  # Location.Back
        self.z_max: float = self.z_size  # Location.Top
        self.bounding_box = {}
        self.position = [0.0, 0.0, 0.0]
        self.rotation = []
        # Placement (task cycax/32): world = T(position) @ _matrix applied to the part's own
        # coordinates. `_local_box` is the part's own box, taken at the first turn/rotate.
        self._matrix = placement.identity()
        self._anchors = {}  # custom and hole anchors (task cycax/37), in part coordinates
        self._local_box = None
        self._only_quarter_turns = True
        self.final_location = False
        self.initial_polygon = polygon
        # The colour: set on the part, else the colour of the material, else the class default.
        self._colour = colour
        self._default_colour = default_colour
        self.material = material
        self.manufacture = manufacture
        self.labels: set[str] = set()
        self.definition()
        self.assembly = assembly
        self.hash = hash
        if assembly:
            assembly.add(self)
            # Assembly will set: part._base_path == assembly._base_path

    @property
    def colour(self):
        if self._colour is not None:
            return self._colour
        if self.material is not None:
            return self.material.colour
        return self._default_colour

    @colour.setter
    def colour(self, value):
        self._colour = value

    @property
    def material(self):
        """The material (cycax.materials.Material) or None."""
        return self._material

    @material.setter
    def material(self, value):
        from cycax.materials import as_material

        self._material = as_material(value)

    @property
    def manufacture(self):
        """How the part is made (cycax.manufacture), or the default of the part class."""
        if self._manufacture is None:
            self._manufacture = self.default_manufacture()
        return self._manufacture

    @manufacture.setter
    def manufacture(self, value):
        from cycax.manufacture import as_manufacture

        self._manufacture = as_manufacture(value)

    def default_manufacture(self):
        """The manufacturing default of this part class (None: no information)."""
        return None

    def definition(self):
        """This method will be ovedridden to do a calculation."""
        pass

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

    def test_mesh_hole(self, x: float, y: float, z: float, diameter: float, depth: float):  # noqa: ARG002 Unused argument
        if (
            x - diameter / 2 < self.x_min
            or x + diameter / 2 > self.x_max
            or y - diameter / 2 < self.y_min
            or y + diameter / 2 > self.y_max
            or depth > self.z_max
        ):
            warnings.warn("This hole may break the mesh of the CycadPart.", stacklevel=2)

    def test_mesh_rectangle_cutout(
        self,
        type: str,  # noqa: A002, ARG002 Shadows builtin, unused argument
        x: float,
        y: float,
        z: float,
        x_size: float,
        y_size: float,
        z_size: float,
        *,
        centered: bool,
    ):
        if centered:
            if (
                x - x_size / 2 < self.x_min
                or x + x_size / 2 > self.x_max
                or y - y_size / 2 < self.y_min
                or y + y_size / 2 > self.y_max
                or z - z_size / 2 < self.z_min
                or z + z_size / 2 > self.z_max
            ):
                warnings.warn("This rectangle cutout may break the mesh of the CycadPart.", stacklevel=2)
        elif (
            x < self.x_min
            or x + x_size > self.x_max
            or y < self.y_min
            or y + y_size > self.y_max
            or z < self.z_min
            or z + z_size > self.z_max
        ):
            warnings.warn("This rectangle cutout may break the mesh of the CycadPart.", stacklevel=2)

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
            self.external_features.append(temp_hole)
        else:
            self.features.append(temp_hole)

    def make_cylinder(
        self,
        x: float,
        y: float,
        z: float,
        side: str,
        diameter: float,
        height: float,
    ):
        """
        If instead of Location.top and Location.bottom it were possible to think rather (x, y, z_max)

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            diameter: The diameter of the hole.
            height: The height of the cylinder.
        """

        cylinder = Cylinder(side=side, x=x, y=y, z=z, diameter=diameter, height=height)
        self.features.append(cylinder)

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
            self.external_features.append(temp_slot.hole_left)
            self.external_features.append(temp_slot.hole_right)
            self.external_features.append(temp_slot.rectangle)
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

    def make_bend(self, feature: Feature):
        """Append a sheet-metal bend/flange feature (see `cycax.cycad.bend`).

        Args:
            feature: The `Bend`, `FlangeCornerRound`, `FlatRectangleCut`, or
                `FlatPolygonCut` feature to add.
        """
        self.features.append(feature)

    def make_sphere_cut_out(self, side: str, x: float, y: float, z: float, diameter: float):
        """This method will insert a sphere into a CycadPart.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            diameter: The Diameter of the sphere.
        """
        temp_sphere = Sphere(side=side, x=x, y=y, z=z, diameter=diameter, cut=True)
        self.features.append(temp_sphere)

    def make_sphere_add(self, side: str, x: float, y: float, z: float, diameter: float):
        """This method will all a sphere onto a part so half of it sticks out.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the hole will be made in.
            diameter: The Diameter of the sphere.
        """
        temp_sphere = Sphere(side=side, x=x, y=y, z=z, diameter=diameter, cut=False)
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
            self.external_features.append(temp_rect)
        else:
            self.features.append(temp_rect)

    def make_rectangle_add(
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
        """This method will add a block on to the CycadPart.

        Args:
            x: Position of feature on X-axis.
            y: Position of feature on Y-axis.
            z: Position of feature on Z-axis.
            side: The side of the part the block will be added onto.
            x_size : The size of x of rectangle.
            y_size : The size of y of rectangle.
            z_size : The size of z of rectangle.
            center : This can be overridden if you would like object centered at origin.
        """

        temp_rect = RectangleAddOn(
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
        # A move by the difference: the minimum corner of the bounding box goes to x, y, z. (The
        # position is not always the minimum corner, e.g. after rotate() about the centre.)
        self.move(
            x=None if x is None else x - self.x_min,
            y=None if y is None else y - self.y_min,
            z=None if z is None else z - self.z_min,
        )

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
    def center(self) -> tuple[float, float, float]:
        """Return the center of a part."""
        # x_min/x_max etc. are absolute coordinates.
        centered_x = (self.x_min + self.x_max) / 2
        centered_y = (self.y_min + self.y_max) / 2
        centered_z = (self.z_min + self.z_max) / 2
        coordinate = namedtuple("Coordinate", ["x", "y", "z"])
        return coordinate(x=centered_x, y=centered_y, z=centered_z)

    def save(self, path: Path | str | None = None) -> Path:
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
        self._base_path = path
        path.mkdir(parents=False, exist_ok=True)

        dir_name = self.path  # Using the path property to ensure it exists
        dir_name.mkdir(exist_ok=True)
        file_path = dir_name / f"{self.part_no}.json"
        file_path = file_path.expanduser().resolve().absolute()
        file_path.write_text(json.dumps(self.export()))
        logging.info("Saved part '%s' to %s", self.part_no, file_path)
        return file_path

    def export(self) -> dict:
        """
        A static representation of the Part, suitable to be saved as JSON (spec version 2).

        The export contains:
            spec_version, kind: 2 and "part".
            name: The part number.
            features: A list of features. features[0] is the base shape. Each feature is a
                dictionary with a type, an action and feature specific fields.
            subtract: Features that are only cut into other parts.
            meta: Information that is not part of the hash: description, notes, doc_view,
                material and colour.

        Returns:
            Static representation of the part.
        """

        dict_out = {"spec_version": SPEC_VERSION, "kind": "part", "name": self.part_no}
        base = getattr(self, "base_feature", None)
        dict_out["features"] = (
            [base()]
            if base
            else [
                {
                    "name": self.initial_polygon,
                    "type": SHAPE_TYPE_MAP[self.initial_polygon],
                    "action": "add",
                    "side": self.side,
                    "x": float(self.x),
                    "y": float(self.y),
                    "z": float(self.z),
                    "x_size": float(self.x_size),
                    "y_size": float(self.y_size),
                    "z_size": float(self.z_size),
                    "center": False,
                }
            ]
        )
        for item in self.features:
            dict_out["features"].append(item.export())
        dict_out["subtract"] = []
        for item in self.external_features:
            dict_out["subtract"].append(item.export())
        dict_out["meta"] = self.export_meta()
        validate_spec(dict_out)
        return dict_out

    def export_meta(self) -> dict:
        """The `meta` object of the part spec: everything that does not change the shape."""
        meta = {"colour": to_rgb(self.colour)}
        for key in ("description", "notes", "doc_view"):
            value = getattr(self, key, None)
            if value:
                meta[key] = value
        if self.material is not None:
            meta["material"] = self.material.to_meta()
        if self.manufacture is not None:
            meta["manufacture"] = self.manufacture.to_meta(self.material)
        if self._anchors:  # custom and named-hole anchors (faces are implied by the base shape)
            meta["anchors"] = {name: anchor.to_meta() for name, anchor in self._anchors.items()}
        return meta

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
        if _eng_lower == "openscad":
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
            msg = f"engine: {engine} is not one of OpenSCAD, Preview3D or FreeCAD."
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

        The part name (or ID) is distinct from the part_no or part number.
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
        # if self.assembly is None:
        #     msg = "Part is not part of an assembly. Please add it to an assembly before using this method."
        #     raise ValueError(msg)
        my_side.level(other_side)
        if subtract:
            other_side.subtract(part2=self)
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

    def turn(self, actions: str):
        """Quarter turns: `part.turn("xxz")` is two quarter turns about x, then one about z.

        Each letter is one 90 degree counter-clockwise turn about that axis. The part keeps its
        minimum corner, so a turn does not move it away from the corner it is levelled to.
        For any angle use `rotate(x=, y=, z=)`.

        Args:
            actions: Letters x, y and z.

        Raises:
            ValueError: When the given actions contains a string that is non x, y, or z.
        """
        for action in actions:
            match action.lower():
                case "x":
                    self.rotate_freeze_left()
                case "y":
                    self.rotate_freeze_front()
                case "z":
                    self.rotate_freeze_top()
                case _:
                    msg = f"""The actions permissible by turn are 'x', 'y' or 'z'.
                            {action} is not one of the permissible actions."""
                    raise ValueError(msg)

    def rotate(self, actions: str | None = None, /, **angles: float):
        """Rotate the part by any angle: `part.rotate(z=30)`, `part.rotate(x=90, z=-15)`.

        Degrees, counter-clockwise (right-hand rule), about the CENTRE of the part's bounding
        box, on the WORLD axes, in the order written. The bounding box afterwards is the box of
        the 8 rotated corners; `level()` uses it.

        Raises:
            TypeError: For the old string form; use `turn("xxz")` for quarter turns.
        """
        if actions is not None:
            msg = f'rotate() takes degrees, e.g. rotate(z=90); use turn("{actions}") for quarter turns.'
            raise TypeError(msg)
        for axis, degrees in angles.items():
            if axis not in ("x", "y", "z"):
                msg = f"rotate() takes x=, y= and z= (degrees), not {axis}=."
                raise TypeError(msg)
            centre = (
                (self.x_min + self.x_max) / 2,
                (self.y_min + self.y_max) / 2,
                (self.z_min + self.z_max) / 2,
            )
            self._apply_world(placement.about(centre, placement.rotation(axis, float(degrees))))
            self.rotation.append({"axis": axis, "angle": float(degrees)})
            if float(degrees) % 90 != 0:
                self._only_quarter_turns = False

    def _take_local_box(self):
        if self._local_box is None:
            p = self.position
            self._local_box = (
                (self.x_min - p[0], self.y_min - p[1], self.z_min - p[2]),
                (self.x_max - p[0], self.y_max - p[1], self.z_max - p[2]),
            )

    def _set_bounds_from_matrix(self):
        lo, hi = placement.bounds(self.placement_matrix(), *self._local_box)
        self.x_min, self.y_min, self.z_min = lo
        self.x_max, self.y_max, self.z_max = hi
        self.make_bounding_box()

    def _apply_world(self, world: placement.Matrix):
        """Apply a world transform to the part (position stays; the matrix takes the change)."""
        self._take_local_box()
        p = self.position
        self._matrix = placement.multiply(
            placement.translation(-p[0], -p[1], -p[2]),
            placement.multiply(world, placement.multiply(placement.translation(*p), self._matrix)),
        )
        self._set_bounds_from_matrix()

    def _quarter_turn(self, axis: str):
        """One quarter turn about `axis` through the origin, then back to the minimum corner (0):
        the same as the engines did with the old rotation list."""
        self._take_local_box()
        turned = placement.multiply(placement.rotation(axis, 90), self._matrix)
        lo, _ = placement.bounds(turned, *self._local_box)
        self._matrix = placement.multiply(placement.translation(*(-v for v in lo)), turned)

    def anchors(self) -> dict:
        """All anchors in PART coordinates: the six faces of the base shape, named holes and
        custom anchors (cycax/37)."""
        from cycax.cycad.anchors import face_anchors  # noqa: PLC0415

        return {**face_anchors((self.x_size, self.y_size, self.z_size)), **self._anchors}

    def ref(self, name: str):
        """A reference to the anchor `name`, for mates: `assembly.align(a.ref("m4"), b.ref("bore"))`."""
        from cycax.cycad.mates import AnchorRef  # noqa: PLC0415

        self.anchor(name)  # an unknown name fails here, with the list of names
        return AnchorRef(self, name)

    def anchor(self, name: str, pos=None, normal=None, x_dir=None):
        """The anchor `name` in WORLD coordinates (it turns and moves with the part).

        With `pos`/`normal` (part coordinates) it first defines a custom anchor:
        `part.anchor("mount", pos=(10, 5, 0), normal=(0, 0, -1), x_dir=(1, 0, 0))`.
        """
        from cycax.cycad.anchors import Anchor  # noqa: PLC0415

        if pos is not None:
            if normal is None:
                msg = "A custom anchor needs a normal."
                raise ValueError(msg)
            self._anchors[name] = Anchor(name, tuple(pos), tuple(normal), tuple(x_dir or _any_perpendicular(normal)))
        anchors = self.anchors()
        if name not in anchors:
            msg = f"{self.part_no} has no anchor {name!r}; it has: {', '.join(sorted(anchors))}."
            raise KeyError(msg)
        return anchors[name].transformed(self.placement_matrix())

    def placement_matrix(self) -> placement.Matrix:
        """The 4 x 4 transform from the part's own coordinates to the world (row-major)."""
        return placement.multiply(placement.translation(*self.position), self._matrix)

    def rotate_freeze_top(self):
        """
        This method will rotate the front and the left while holding the top where it currently is.
        """
        self._quarter_turn("z")
        self.rotation.append({"axis": "z", "angle": 90})
        # The box of the turned part, from the placement (the old min/max swap was wrong for a
        # part that was moved before the turn).
        self._set_bounds_from_matrix()

    def rotate_freeze_left(self):
        """
        This method will rotate the top and front while holding the left where it currently is.
        """
        self._quarter_turn("x")
        self.rotation.append({"axis": "x", "angle": 90})
        # The box of the turned part, from the placement (the old min/max swap was wrong for a
        # part that was moved before the turn).
        self._set_bounds_from_matrix()

    def rotate_freeze_front(self):
        """
        This method will rotate the left and top while holding the front where it currently is.
        """
        self._quarter_turn("y")
        self.rotation.append({"axis": "y", "angle": 90})
        # The box of the turned part, from the placement (the old min/max swap was wrong for a
        # part that was moved before the turn).
        self._set_bounds_from_matrix()

    def _final_place(self):
        """
        It is used to move the external_features to their final location before they are subtracted from
        the other part.
        """
        if self.external_features and not self._only_quarter_turns:
            msg = (
                f"{self.part_no}: subtract() of a part rotated by an angle that is not a multiple of 90 "
                "degrees is not supported yet."
            )
            raise NotImplementedError(msg)
        for feature in self.external_features:
            temp_feature = copy.deepcopy(feature)
            rotation = [self.x_size, self.y_size, self.z_size]
            for rot in self.rotation:
                if rot["axis"] == "x":
                    rotation = temp_feature.swap_yz(rot=1, rotmax=rotation)
                elif rot["axis"] == "y":
                    rotation = temp_feature.swap_xz(rot=1, rotmax=rotation)
                elif rot["axis"] == "z":
                    rotation = temp_feature.swap_xy(rot=1, rotmax=rotation)
            if self.position[0] != 0:
                temp_feature.move(x=self.position[0])
            if self.position[1] != 0:
                temp_feature.move(y=self.position[1])
            if self.position[2] != 0:
                temp_feature.move(z=self.position[2])
            yield temp_feature

    def merge(self, part2: CycadPart):
        """
        This method will be used to merge this part and another part together.
        which have identical sizes but different features.
        This part will receive the features of part2 and part2 its features.

        Args:
            part2: This part will receive the features present on part1.

        Raises:
            ValueError: if the sizes of the parts are not identical.
        """
        if self.x_size == part2.x_size and self.y_size == part2.y_size and self.z_size == part2.z_size:
            for item in part2.features:
                if item not in self.features:
                    self.features.append(item)
            for item in part2.external_features:
                if item not in self.external_features:
                    self.external_features.append(item)
            part2.features = self.features
            part2.external_features = self.external_features
        else:
            msg = f"merging {self} and {part2} but they are not of the same size."
            raise ValueError(msg)


def _any_perpendicular(normal) -> tuple[float, float, float]:
    """An x direction for an anchor that has only a normal."""
    nx, ny, nz = normal
    candidate = (1.0, 0.0, 0.0) if abs(nx) < 0.9 else (0.0, 1.0, 0.0)  # noqa: PLR2004
    dot = nx * candidate[0] + ny * candidate[1] + nz * candidate[2]
    x = [c - dot * n for c, n in zip(candidate, normal, strict=True)]
    length = sum(v * v for v in x) ** 0.5
    return tuple(v / length for v in x)
