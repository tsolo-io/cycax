# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import typing

from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP, Location

# Maps the internal shape label (historically stored in `name`) to the data-file-spec `type`
# value, and the internal add/cut action (historically stored in `type`) to the spec `action`
# value. See docs/content/data-file-part-spec-features.md.
SHAPE_TYPE_MAP: dict[str, str] = {
    "hole": "cylinder",
    "cylinder_feature": "cylinder",
    "cylinder": "cylinder",
    "cube": "cuboid",
    "nut": "nut_cutout",
    "sphere": "sphere",
    "beveled_edge": "beveled_edge",
    "external": "external",
    "bend": "bend",
    "flange_corner_round": "flange_corner_round",
    "flat_rectangle_cut": "flat_rectangle_cut",
    "flat_polygon_cut": "flat_polygon_cut",
    "flange_hole_cut": "flange_hole_cut",
}
ACTION_MAP: dict[str, str] = {"cut": "subtract", "add": "add", "bend": "bend"}


class Feature(Location):
    """The Parent class of all features,"""

    def __repr__(self) -> str:
        return f"Feature(name={self.name}, type={self.type}, x={self.x}, y={self.y}, z={self.z}, side={self.side})"

    def export(self) -> dict:
        """Create a dictionary holding a representation of the feature.

        Returns:
            A serialised representation of the feature.

        Raises:
            AttributeError: When name or type is not defined on the feature.
        """

        feature_dict = {}
        for key in ("name", "type"):
            getattr(self, key)  # Just get the attribute and let Python raise attribute error if it does not exists.

        for key, value in vars(self).items():
            if not key.startswith("_"):
                # Save all the public variables of the feature.
                feature_dict[key] = value

        for key in ("x", "y", "z", "x_size", "y_size", "z_size", "diameter"):
            if key in feature_dict:
                feature_dict[key] = float(feature_dict[key])

        feature_dict["action"] = ACTION_MAP[self.type]
        feature_dict["type"] = SHAPE_TYPE_MAP[self.name]

        return feature_dict


class Holes(Feature):
    """This class will store data on holes. A hole is a cylinder cut into an object.
    This class will initialize a hole at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the object that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter: Diameter of the hole.
        depth: depth of the hole.

    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float, depth: float):
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter
        self.depth = depth
        self.name = "hole"
        self.type = "cut"


class Cylinder(Feature):
    """This class will store data on cylinders. A Cylinder is added to an object.
    This class will initialize a cylinder at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the object that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter: Diameter of the cylinder.
        height: Height of the cylinder.

    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float, height: float):
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter
        self.depth = height
        self.name = "cylinder_feature"
        self.type = "add"


class RectangleCutOut(Feature):
    """This class can be used for cutting a hole that is not round but rather of the defined parameters.

    This class is a hole that is not round.
    The location refers to its bottom left hand corner.

    This class will initialize a Rectangle Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        x_size: x_size of the rectangle.
        y_size: y_size of the rectangle.
        z_size: z_size of the rectangle.
        center: This can be over ridden to instead specify the rectangle's location from its center.
    """

    def __init__(
        self,
        side: str,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        x_size: float = 0,
        z_size: float = 0,
        y_size: float = 2,
        *,
        center: bool = False,
    ):
        Location.__init__(self, x, y, z, side)
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.center = center
        self.name = "cube"
        self.type = "cut"

    def __calc__(self):
        if self.side in (FRONT, LEFT, BOTTOM):
            self.x += self.x_size / 2
            self.y += self.y_size / 2
            self.z += self.z_size / 2
        elif self.side == BACK:
            self.x += self.x_size / 2
            self.y -= self.y_size / 2
            self.z += self.z_size / 2
        elif self.side == RIGHT:
            self.x -= self.x_size / 2
            self.y += self.y_size / 2
            self.z += self.z_size / 2
        else:  # side = TOP
            self.x += self.x_size / 2
            self.y += self.y_size / 2
            self.z -= self.z_size / 2
        self.center = True

    def swap_xy(self, rot: float, rotmax: list) -> list:
        """
        This will rotate slot while holding top where it is. It overrides the method present in the location super.

        Args:
            rot: the number of times to perform the swap.
            rotmax: the maximum values for the swap.

        Returns:
            New location of relevant max of (x,y,z). useful when doing repeated swaps.
        """
        rotmax = super().swap_xy(rot=rot, rotmax=rotmax)
        while rot > 0:
            self.x_size, self.y_size = self.y_size, self.x_size
            rot = rot - 1
        return rotmax

    def swap_xz(self, rot: float, rotmax: list) -> list:
        """This will rotate slot while holding front where it is. It overrides the method present in the location super.

        Args:
            rot: the number of times to perform the swap.
            rotmax: the maximum values for the swap.

        Returns:
            New location of relevant max of (x,y,z). useful when doing repeated swaps.
        """
        rotmax = super().swap_xz(rot=rot, rotmax=rotmax)
        while rot > 0:
            self.x_size, self.z_size = self.z_size, self.x_size
            rot = rot - 1
        return rotmax

    def swap_yz(self, rot: float, rotmax: list) -> list:
        """This will rotate slot while holding left where it is. It overrides the method present in the location super.

        Args:
            rot: the number of times to perform the swap.
            rotmax: the maximum values for the swap.

        Returns:
            New location of relevant max of (x,y,z). useful when doing repeated swaps.
        """
        rotmax = super().swap_yz(rot=rot, rotmax=rotmax)
        while rot > 0:
            self.y_size, self.z_size = self.z_size, self.y_size
            rot = rot - 1

        return rotmax


class RectangleAddOn(RectangleCutOut):
    """This class can be used for cutting a hole that is not round but rather of the defined parameters.

    This class is a hole that is not round.
    The location refers to its bottom left hand corner.

    This class will initialize a Rectangle Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        x_size: x_size of the rectangle.
        y_size: y_size of the rectangle.
        z_size: z_size of the rectangle.
        center: This can be over ridden to instead specify the rectangle's location from its center.
    """

    def __init__(
        self,
        side: str,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        x_size: float = 0,
        z_size: float = 0,
        y_size: float = 2,
        *,
        center: bool = False,
    ):
        Location.__init__(self, x, y, z, side)
        self.x_size = x_size
        self.y_size = y_size
        self.z_size = z_size
        self.center = center
        self.name = "cube"
        self.type = "add"
        self.__calc__()

    def __calc__(self):
        if self.side in (BACK, RIGHT, TOP):
            self.x += self.x_size / 2
            self.y += self.y_size / 2
            self.z += self.z_size / 2
        elif self.side == FRONT:
            self.x += self.x_size / 2
            self.y -= self.y_size / 2
            self.z += self.z_size / 2
        elif self.side == LEFT:
            self.x -= self.x_size / 2
            self.y += self.y_size / 2
            self.z += self.z_size / 2
        else:  # side = BOTTOM
            self.x += self.x_size / 2
            self.y += self.y_size / 2
            self.z -= self.z_size / 2
        self.center = True


class NutCutOut(Feature):
    """
    Class for holding the data for nut cut outs.
    The nut cut outs will allow us to hold nuts in 3D printed plastic.

    This class will initialize a Nut Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        nut_type: Type of nut to be inserted.
        depth: depth of the nut.
        vertical: this is a bool that will be set to False if you want the flat side down.
    """

    nut_specifications: typing.ClassVar[
        dict[str, dict[str, float]]
    ] = {  # This is a global variable that will be used to cut the nuts by the OpenSCAD engine.
        "M3ISO": {
            "diameter": 6.01,
            "thickness": 2.4,
            "side_to_side": 5.4,
        },
        "M3": {
            "diameter": 6.2,
            "thickness": 2.5,
            "side_to_side": 5.5,
        },
        "M6ISO": {
            "diameter": 11.05,
            "thickness": 5.2,
            "side_to_side": 10,
        },
    }

    def __init__(
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
        self.name = "nut"
        self.type = "cut"
        Location.__init__(self, x, y, z, side)
        self.nut_type = nut_type.upper()
        self.diameter = NutCutOut.nut_specifications[self.nut_type]["diameter"]
        self.thickness = NutCutOut.nut_specifications[self.nut_type]["thickness"]
        self.side_to_side = NutCutOut.nut_specifications[self.nut_type]["side_to_side"]
        if depth is None:
            self.depth = self.thickness
        else:
            self.depth = depth
        self.vertical = vertical


class Sphere(Feature):
    """
    Class for holding the data for sphere cut outs.

    This class will initialize a Sphere Cut Out at the desired location.

    Args:
        x: The location of x along the x axis.
        y: The location of y along the y axis.
        z: The location of z along the z axis.
        side: The side of the odject that this location refers to.
            This will be used to specify from which side a feature should be inserted into another object.
            This will be one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK.
        diameter: diameter of the sphere.
    """

    def __init__(self, side: str, x: float, y: float, z: float, diameter: float, *, cut: bool):
        self.name = "sphere"
        if cut:
            self.type = "cut"
        else:
            self.type = "add"
        Location.__init__(self, x, y, z, side)
        self.diameter = diameter


class Bend(Feature):
    """A sheet-metal bend/flange feature.

    See docs/content/bending-design.md for the full design. Orientation is stored as
    `u_dir` (along the fold line, the flange's "width" direction), `v_dir` (away from the
    fold, the direction the flange extends) and `n_dir` (outward face normal, the
    thickness direction) -- three vectors rather than an angle-and-axis pair, since the
    rotation axis (`u_dir`) is not necessarily a global X/Y/Z axis once bends are nested,
    and only `u_dir`/`v_dir`/`n_dir` are enough for any future engine to reconstruct exact
    geometry without re-deriving it from the semantic fields.

    `x`/`y`/`z` (via `Location`) are the origin corner of the fold line (u=0, v=0).

    Args:
        side: The named side this bend was made from (unchanged through a `.far` chain --
            see bending-design.md open question #1; only "the far edge" chaining is
            currently supported, so the root side name identifies the whole chain).
        u_dir: Unit vector along the fold line.
        v_dir: Unit vector the flange extends along, away from the fold.
        n_dir: Unit vector normal to the flange's face.
        fold_dir: The *parent* flange's own extension direction (i.e. what `v_dir` was
            for whatever this bend was made from, before this bend's own rotation) --
            distinct from `v_dir` above, which is this bend's own, already-rotated
            direction. Needed only by the FreeCAD engine (`cycax_part_freecad.py`) to
            locate this bend's fold-line edge on the real, rounded-bend-radius geometry:
            verified empirically that cycax's own idealised zero-radius coordinates don't
            exactly match FreeCAD SheetMetal's real bend geometry, so the engine searches
            for "the matching edge furthest along `fold_dir`" instead of an exact
            coordinate match -- and searching along this bend's own `v_dir` picks the
            wrong axis entirely for a nested bend (confirmed by hand before adding this
            field, not assumed).
        width: Extent along `u_dir`.
        height: Extent along `v_dir` -- the flange's own flat length.
        thickness: Sheet thickness -- material spans this in the `-n_dir` direction from
            the origin (carried on the feature so an engine never needs to reach back into
            the base feature for it -- "verbose by design", data-file-spec-new.md).
        angle: Bend angle in degrees, already resolved to a positive magnitude (see
            `cycax.cycad.bend.resolve_bend_angle`).
        direction: `"up"` or `"down"`, already resolved.
        radius: Inside bend radius.
        k_factor: Bend-allowance K-factor.
        gap1: Relief at the start of the bend line (along `u_dir` from the parent edge).
        gap2: Relief at the end of the bend line.
        corner_reference: Where the bend's corner offset sits -- `"outer"` (default),
            `"inner"`, `"thickness_outer"`, or `"offset"` (matches FreeCAD SheetMetal's
            `BendType`; see bending-design.md).
        length_spec: Where along the flange `height` is measured to -- `"leg"` (default),
            `"outer_sharp"`, `"inner_sharp"`, or `"tangential"` (matches FreeCAD
            SheetMetal's `LengthSpec`).
        label: DXF annotation text. Auto-generated from `angle`/`direction` when omitted.
        parent: `id` of the `Bend` feature this one was bent from, or `None` for a bend
            made directly off the base sheet.
        bend_id: This feature's own identifier, so a child bend can reference it via
            `parent`. Deterministically assigned (a counter, not a random UUID) so the
            exported JSON -- and its build-cache hash -- stays reproducible.
    """

    def __init__(
        self,
        *,
        side: str,
        x: float,
        y: float,
        z: float,
        u_dir: tuple[float, float, float],
        v_dir: tuple[float, float, float],
        n_dir: tuple[float, float, float],
        fold_dir: tuple[float, float, float],
        width: float,
        height: float,
        thickness: float,
        angle: float,
        direction: str,
        radius: float,
        k_factor: float,
        bend_id: str,
        gap1: float = 0.0,
        gap2: float = 0.0,
        corner_reference: str = "outer",
        length_spec: str = "leg",
        label: str | None = None,
        parent: str | None = None,
    ):
        Location.__init__(self, x, y, z, side)
        self.u_dir = list(u_dir)
        self.v_dir = list(v_dir)
        self.n_dir = list(n_dir)
        self.fold_dir = list(fold_dir)
        self.width = width
        self.height = height
        self.thickness = thickness
        self.angle = angle
        self.direction = direction
        self.radius = radius
        self.k_factor = k_factor
        self.gap1 = gap1
        self.gap2 = gap2
        self.corner_reference = corner_reference
        self.length_spec = length_spec
        self.label = label if label is not None else f"{angle:g}\N{DEGREE SIGN} {direction.upper()}"
        self.parent = parent
        self.id = bend_id
        self.name = "bend"
        self.type = "bend"


class FlangeCornerRound(Feature):
    """Rounds the two far corners of a sheet-metal flange (a terminal bend).

    Deliberately not `BeveledEdge` (`beveled_edge.py`) -- sheet-metal corner rounding is
    kept as its own, dedicated mechanism rather than sugar over the generic edge-bevel
    primitive, even though the two happen to cut similar-looking geometry (see
    docs/content/bending-design.md §11 and the "dedicated over generic reuse" decision
    behind it).

    Args:
        side: The flange's named side (see `Bend.side`).
        u_dir: Unit vector along the flange's fold line, at the far edge.
        v_dir: Unit vector the flange extends along -- the corners rounded are at
            `x`/`y`/`z` + `width` * `u_dir`, on the far (`v_dir`-extreme) edge.
        n_dir: Unit vector normal to the flange's face.
        width: Extent along `u_dir`, i.e. the span between the two corners being rounded.
        thickness: Sheet thickness (see `Bend.thickness`).
        radius: Radius of the round.
        parent: `id` of the `Bend` feature this flange was created by.
    """

    def __init__(
        self,
        *,
        side: str,
        x: float,
        y: float,
        z: float,
        u_dir: tuple[float, float, float],
        v_dir: tuple[float, float, float],
        n_dir: tuple[float, float, float],
        width: float,
        thickness: float,
        radius: float,
        parent: str | None,
    ):
        Location.__init__(self, x, y, z, side)
        self.u_dir = list(u_dir)
        self.v_dir = list(v_dir)
        self.n_dir = list(n_dir)
        self.width = width
        self.thickness = thickness
        self.radius = radius
        self.parent = parent
        self.name = "flange_corner_round"
        self.type = "cut"


class FlatRectangleCut(Feature):
    """A straight-through rectangular cutout on a flat sheet-metal face (base sheet or a
    flange).

    Laser-cut sheet metal is always cut on the flat, so every cutout is a straight-through
    2D shape (see docs/content/sheetmetal-bend-design.md) rather than a 3D pocket -- unlike
    `RectangleCutOut`, which supports depth/sink for 3D-printed/CNC parts. Rotation is not
    a separate stored field: `u_dir`/`v_dir` are this shape's own (possibly rotated) local
    axes, already resolved to their final direction by the caller (see
    `cycax.cycad.bend.BendSide.rectangle`), the same way `Bend.v_dir` bakes in its own
    cumulative angle instead of storing "angle" as a separately-interpreted field.

    Args:
        side: The named side this cut is on (see `Bend.side`).
        x/y/z: The rectangle's own centre.
        u_dir: Unit vector along the rectangle's own (rotated) width axis.
        v_dir: Unit vector along the rectangle's own (rotated) height axis.
        n_dir: Unit vector normal to the face (the thickness direction).
        width: Extent along `u_dir`.
        height: Extent along `v_dir`.
        thickness: Sheet thickness -- the cut spans this in the `-n_dir` direction from the
            centre (straight through).
        parent: `id` of the `Bend` feature this cut is on, or `None` for the base sheet.
    """

    def __init__(
        self,
        *,
        side: str,
        x: float,
        y: float,
        z: float,
        u_dir: tuple[float, float, float],
        v_dir: tuple[float, float, float],
        n_dir: tuple[float, float, float],
        width: float,
        height: float,
        thickness: float,
        parent: str | None,
    ):
        Location.__init__(self, x, y, z, side)
        self.u_dir = list(u_dir)
        self.v_dir = list(v_dir)
        self.n_dir = list(n_dir)
        self.width = width
        self.height = height
        self.thickness = thickness
        self.parent = parent
        self.name = "flat_rectangle_cut"
        self.type = "cut"


class FlangeHoleCut(Feature):
    """A straight-through circular hole on a flat sheet-metal face (base sheet or a flange).

    Same oriented `u_dir`/`v_dir`/`n_dir`/`parent` shape as `FlatRectangleCut`/
    `FlatPolygonCut` -- deliberately a separate, dedicated feature rather than reusing the
    generic, part-type-agnostic `Holes` (see the "dedicated over generic reuse" decision):
    `parent` is what lets the FreeCAD engine look up which `Bend` this hole sits on and
    correct for that bend's real (rounded-radius) geometry offset from cycax's idealised
    position (`u_dir`/`v_dir` don't carry rotation for a circle, but `parent` still matters).

    Args:
        side: The named side this cut is on (see `Bend.side`).
        x/y/z: The hole's own centre.
        u_dir: Unit vector along the flange's own local width axis (informational only for
            a circle, kept for symmetry with `FlatRectangleCut`/`FlatPolygonCut`).
        v_dir: Unit vector along the flange's own local height axis.
        n_dir: Unit vector normal to the face (the thickness direction).
        diameter: Hole diameter.
        thickness: Sheet thickness, or an explicit drilled depth if shallower.
        parent: `id` of the `Bend` feature this hole is on, or `None` for the base sheet.
    """

    def __init__(
        self,
        *,
        side: str,
        x: float,
        y: float,
        z: float,
        u_dir: tuple[float, float, float],
        v_dir: tuple[float, float, float],
        n_dir: tuple[float, float, float],
        diameter: float,
        thickness: float,
        parent: str | None,
    ):
        Location.__init__(self, x, y, z, side)
        self.u_dir = list(u_dir)
        self.v_dir = list(v_dir)
        self.n_dir = list(n_dir)
        self.diameter = diameter
        self.thickness = thickness
        self.parent = parent
        self.name = "flange_hole_cut"
        self.type = "cut"


class FlatPolygonCut(Feature):
    """A straight-through regular-polygon cutout on a flat sheet-metal face (base sheet or
    a flange).

    Sized by `diameter` (the circumscribed circle) rather than side length, and oriented
    the same way as the (aspirational, not-yet-implemented-elsewhere) `regular_polygon`
    JSON feature in docs/content/data-file-part-spec-features.md: with no rotation applied,
    one vertex sits at the minimum point along `v_dir` -- `v_dir` plays the role that global
    `-y` plays there. As with `FlatRectangleCut`, rotation is baked into `u_dir`/`v_dir` by
    the caller rather than stored as a separate field.

    Args:
        side: The named side this cut is on (see `Bend.side`).
        x/y/z: The polygon's own centre.
        u_dir: Unit vector along the polygon's own (rotated) local X axis.
        v_dir: Unit vector along the polygon's own (rotated) local Y axis (one vertex sits
            at this axis's minimum before any further rotation).
        n_dir: Unit vector normal to the face (the thickness direction).
        sides: Number of sides, an integer > 2.
        diameter: Diameter of the circumscribed circle.
        thickness: Sheet thickness -- the cut spans this in the `-n_dir` direction from the
            centre (straight through).
        parent: `id` of the `Bend` feature this cut is on, or `None` for the base sheet.
    """

    def __init__(
        self,
        *,
        side: str,
        x: float,
        y: float,
        z: float,
        u_dir: tuple[float, float, float],
        v_dir: tuple[float, float, float],
        n_dir: tuple[float, float, float],
        sides: int,
        diameter: float,
        thickness: float,
        parent: str | None,
    ):
        min_polygon_sides = 3
        if sides < min_polygon_sides:
            msg = f"sides must be > 2, got {sides}."
            raise ValueError(msg)
        Location.__init__(self, x, y, z, side)
        self.u_dir = list(u_dir)
        self.v_dir = list(v_dir)
        self.n_dir = list(n_dir)
        self.sides = sides
        self.diameter = diameter
        self.thickness = thickness
        self.parent = parent
        self.name = "flat_polygon_cut"
        self.type = "cut"
