# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Sheet-metal bending: angle/direction resolution and the chainable `BendSide`.

See docs/content/bending-design.md for the full design.

Known limitation of this implementation, not yet lifted: only chaining off a flange's
*far* edge (`BendSide.far`, opposite the fold that created it) is supported. Bending off
one of a flange's own side edges (`.left`/`.right`/`.front`/`.back` on a `BendSide`) needs
full 3D re-orientation tracking that isn't implemented yet -- those raise
`NotImplementedError` rather than silently producing wrong geometry. Every bend chain's
rotation axis (`u_dir`) is therefore fixed for its whole chain, which keeps the geometry
to a single rotating (`v_dir`, `n_dir`) plane per chain -- see `_v_dir`/`_n_dir`.
"""

import math

from cycax.cycad.features import Bend, FlangeCornerRound, FlangeHoleCut, FlatPolygonCut, FlatRectangleCut
from cycax.cycad.location import BACK, FRONT, LEFT, RIGHT

VALID_DIRECTIONS = ("up", "down")
MAX_BEND_ANGLE = 180.0

# The direction a side's own edge extends in *before* any bend (the flat, unfolded state).
_FLAT_DIRECTIONS = {
    FRONT: (0.0, -1.0, 0.0),
    BACK: (0.0, 1.0, 0.0),
    LEFT: (-1.0, 0.0, 0.0),
    RIGHT: (1.0, 0.0, 0.0),
}
# The direction along that side's own fold line (its "width" axis) -- unchanged for the
# whole chain, since only far-edge chaining is supported (see module docstring).
_U_DIRECTIONS = {
    FRONT: (1.0, 0.0, 0.0),
    BACK: (1.0, 0.0, 0.0),
    LEFT: (0.0, 1.0, 0.0),
    RIGHT: (0.0, 1.0, 0.0),
}
_Z_HAT = (0.0, 0.0, 1.0)
_AXIS_TOLERANCE = 1e-6


def resolve_bend_angle(angle: float, direction: str | None = None) -> tuple[float, str]:
    """Resolve a bend's angle/direction into their normalised form.

    `direction` defaults to `"up"` when not given. A negative `angle` flips whichever
    direction is in effect (the given one, or the `"up"` default), rather than being an
    error: bend angles sometimes come out of an equation rather than being typed in by
    hand, and can legitimately come out negative (e.g. -45) without the caller having
    special-cased the sign themselves. Two negatives cancel: `angle=-90` with
    `direction="down"` resolves to `(90.0, "up")`.

    Args:
        angle: Bend angle in degrees. May be negative (see above). Magnitude must be at
            most `MAX_BEND_ANGLE` (180) degrees.
        direction: `"up"` or `"down"` (case-insensitive), or `None` to default to `"up"`.

    Returns:
        `(magnitude, direction)` with `magnitude >= 0` and `direction` one of
        `"up"`/`"down"`.

    Raises:
        ValueError: If `direction` is not one of `"up"`/`"down"`, or the angle's
            magnitude exceeds `MAX_BEND_ANGLE` degrees.
    """
    direction = "up" if direction is None else direction.lower()
    if direction not in VALID_DIRECTIONS:
        msg = f"direction={direction!r} is not one of {VALID_DIRECTIONS}."
        raise ValueError(msg)

    if angle < 0:
        direction = "down" if direction == "up" else "up"
        angle = -angle

    if angle > MAX_BEND_ANGLE:
        msg = f"angle magnitude {angle} exceeds the maximum bend angle of {MAX_BEND_ANGLE} degrees."
        raise ValueError(msg)

    return float(angle), direction


def _offset(origin: tuple[float, float, float], *pairs: tuple[tuple[float, float, float], float]):
    """Move `origin` by `distance` along `direction`, for each `(direction, distance)` pair."""
    x, y, z = origin
    for direction, distance in pairs:
        x += direction[0] * distance
        y += direction[1] * distance
        z += direction[2] * distance
    return (_clean(x), _clean(y), _clean(z))


_ROUND_DIGITS = 9  # Clears sin()/cos() float noise (e.g. 1e-16) without losing real precision.


def _clean(value: float) -> float:
    """Round away sin()/cos() float noise and normalise -0.0 to 0.0."""
    return round(value, _ROUND_DIGITS) + 0.0


def _v_dir(flat_dir: tuple[float, float, float], angle_rad: float) -> tuple[float, float, float]:
    """The direction a flange extends in, `angle_rad` (signed, "up" positive) from flat."""
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    x, y, z = (flat_dir[i] * cos_a + _Z_HAT[i] * sin_a for i in range(3))
    return (_clean(x), _clean(y), _clean(z))


def _n_dir(flat_dir: tuple[float, float, float], angle_rad: float) -> tuple[float, float, float]:
    """The flange's outward face normal, `angle_rad` (signed, "up" positive) from flat."""
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    x, y, z = (-flat_dir[i] * sin_a + _Z_HAT[i] * cos_a for i in range(3))
    return (_clean(x), _clean(y), _clean(z))


def _rotate_in_plane(
    u_dir: tuple[float, float, float], v_dir: tuple[float, float, float], angle_deg: float
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Rotate the `(u_dir, v_dir)` axis pair by `angle_deg` within their own plane.

    Used to bake a cutout's `angle` into its own local axes at authoring time (see
    `FlatRectangleCut`/`FlatPolygonCut`), rather than carrying "angle" as a field engines
    would need to interpret.
    """
    if angle_deg == 0.0:
        return u_dir, v_dir
    angle_rad = math.radians(angle_deg)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    new_u = tuple(u_dir[i] * cos_a + v_dir[i] * sin_a for i in range(3))
    new_v = tuple(-u_dir[i] * sin_a + v_dir[i] * cos_a for i in range(3))
    return tuple(_clean(c) for c in new_u), tuple(_clean(c) for c in new_v)


def _side_for_normal(n_dir: tuple[float, float, float]) -> str:
    """Snap an axis-aligned `n_dir` to one of the six named sides.

    Only correct when `n_dir` is (very close to) a global X/Y/Z axis -- i.e. the flange's
    cumulative bend angle is a multiple of 90 degrees. Used only by `BendSide.hole()`,
    which needs a named side to reuse the existing `CycadPart.make_hole()`.
    """
    axis_sides = {
        (0.0, 0.0, 1.0): "TOP",
        (0.0, 0.0, -1.0): "BOTTOM",
        (0.0, 1.0, 0.0): "BACK",
        (0.0, -1.0, 0.0): "FRONT",
        (1.0, 0.0, 0.0): "RIGHT",
        (-1.0, 0.0, 0.0): "LEFT",
    }
    for axis, side in axis_sides.items():
        if all(abs(n_dir[i] - axis[i]) < _AXIS_TOLERANCE for i in range(3)):
            return side
    msg = (
        f"n_dir={n_dir} is not axis-aligned -- holes on a flange are only supported when "
        "its face is axis-aligned (the chain's cumulative bend angle is a multiple of 90 "
        "degrees)."
    )
    raise NotImplementedError(msg)


class BendSide:
    """A chainable, bendable flange -- or, at the root of a chain, one of a SheetMetal
    part's own LEFT/RIGHT/FRONT/BACK sides.

    Not a `CycadSide` subclass: `CycadSide`'s per-side geometry is axis-aligned-box
    specific (`_location_calc`/`_box_size_calc`, keyed to the part's own
    `x_min`/`x_max`/etc.), whereas a flange's geometry is an arbitrary oriented plane --
    tracked here as an origin point plus (`u_dir`, `v_dir`, `n_dir`): `u_dir` along the
    fold line ("width"), `v_dir` along the flange away from its fold ("length"), `n_dir`
    the outward face normal (thickness direction). Public methods (`hole`, `bend`,
    `round_corners`, `far`) are named to match `CycadSide`'s own idiom, not inherited
    from it.
    """

    def __init__(
        self,
        part,
        *,
        side: str,
        origin: tuple[float, float, float],
        u_dir: tuple[float, float, float],
        v_dir: tuple[float, float, float],
        n_dir: tuple[float, float, float],
        flat_dir: tuple[float, float, float],
        width: float,
        height: float,
        thickness: float,
        cumulative_angle: float,
        bend_id: str | None,
    ):
        self._part = part
        self.side = side
        self.origin = origin
        self.u_dir = u_dir
        self.v_dir = v_dir
        self.n_dir = n_dir
        self._flat_dir = flat_dir
        self.width = width
        self.height = height  # This flange's own flat length; 0 for a bare root side.
        self.thickness = thickness
        self._cumulative_angle = cumulative_angle
        self.bend_id = bend_id  # id of the Bend feature that produced this flange, or None at the root.
        self._terminal = False

    def __enter__(self) -> "BendSide":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    @property
    def far(self) -> "BendSide":
        """The edge opposite this flange's own fold line -- the common case for chaining."""
        return self

    def _unsupported_side(self, name: str):
        msg = (
            f"Bending off a flange's own {name} edge is not yet implemented -- only "
            "chaining off the far edge (`.far`) is currently supported. See the module "
            "docstring in cycax.cycad.bend."
        )
        raise NotImplementedError(msg)

    @property
    def left(self):
        self._unsupported_side("left")

    @property
    def right(self):
        self._unsupported_side("right")

    @property
    def front(self):
        self._unsupported_side("front")

    @property
    def back(self):
        self._unsupported_side("back")

    def _next_bend_id(self) -> str:
        self._part._bend_counter = getattr(self._part, "_bend_counter", 0) + 1
        return f"bend_{self._part._bend_counter}"

    def bend(
        self,
        angle: float,
        height: float,
        *,
        direction: str | None = None,
        radius: float | None = None,
        k_factor: float | None = None,
        gap1: float = 0.0,
        gap2: float = 0.0,
        corner_reference: str = "outer",
        length_spec: str = "leg",
        label: str | None = None,
    ) -> "BendSide":
        """Add a bend/flange, folding from this side's (or flange's far edge's) fold line.

        Args:
            angle: Bend angle in degrees. May be negative (see `resolve_bend_angle`).
            height: The new flange's own flat length.
            direction: `"up"` or `"down"`; defaults to `"up"` (see `resolve_bend_angle`).
            radius: Inside bend radius; defaults to the part's `bend_radius`.
            k_factor: Bend-allowance K-factor; defaults to the part's `k_factor`.
            gap1: Relief at the start of the bend line.
            gap2: Relief at the end of the bend line.
            corner_reference: See `Bend.corner_reference`.
            length_spec: See `Bend.length_spec`.
            label: DXF annotation text; auto-generated from `angle`/`direction` if omitted.

        Raises:
            ValueError: If this flange's corners have already been rounded (terminal), or
                `gap1 + gap2` leaves no width for the flange.
        """
        if self._terminal:
            msg = "Cannot bend a flange whose corners have already been rounded (round_corners() marks it terminal)."
            raise ValueError(msg)

        angle, direction = resolve_bend_angle(angle, direction)
        signed_angle = angle if direction == "up" else -angle
        new_cumulative = self._cumulative_angle + signed_angle
        angle_rad = math.radians(new_cumulative)
        new_v_dir = _v_dir(self._flat_dir, angle_rad)
        new_n_dir = _n_dir(self._flat_dir, angle_rad)

        new_width = self.width - gap1 - gap2
        if new_width <= 0:
            msg = f"gap1 ({gap1}) + gap2 ({gap2}) leaves no width on a {self.width} mm-wide edge."
            raise ValueError(msg)
        new_origin = _offset(self.origin, (self.v_dir, self.height), (self.u_dir, gap1))

        part = self._part
        radius = part.bend_radius if radius is None else radius
        k_factor = part.k_factor if k_factor is None else k_factor
        if radius is None or k_factor is None:
            msg = "bend() needs a radius/k_factor, either passed in or set on the SheetMetal part."
            raise ValueError(msg)

        bend_id = self._next_bend_id()
        feature = Bend(
            side=self.side,
            x=new_origin[0],
            y=new_origin[1],
            z=new_origin[2],
            u_dir=self.u_dir,
            v_dir=new_v_dir,
            n_dir=new_n_dir,
            fold_dir=self.v_dir,
            width=new_width,
            height=height,
            thickness=self.thickness,
            angle=angle,
            direction=direction,
            radius=radius,
            k_factor=k_factor,
            gap1=gap1,
            gap2=gap2,
            corner_reference=corner_reference,
            length_spec=length_spec,
            label=label,
            parent=self.bend_id,
            bend_id=bend_id,
        )
        part.make_bend(feature)
        _grow_part_bounds(part, new_origin, self.u_dir, new_v_dir, new_n_dir, new_width, height, self.thickness)

        return BendSide(
            part,
            side=self.side,
            origin=new_origin,
            u_dir=self.u_dir,
            v_dir=new_v_dir,
            n_dir=new_n_dir,
            flat_dir=self._flat_dir,
            width=new_width,
            height=height,
            thickness=self.thickness,
            cumulative_angle=new_cumulative,
            bend_id=bend_id,
        )

    def round_corners(self, radius: float) -> "BendSide":
        """Round this flange's two far corners, and mark it terminal (no further `bend()`).

        Deliberately not `CycadPart.beveled_edge()` -- see `FlangeCornerRound`.
        """
        if self.height <= 0:
            msg = "round_corners() needs a flange that has actually been bent (height > 0)."
            raise ValueError(msg)

        far_origin = _offset(self.origin, (self.v_dir, self.height))
        feature = FlangeCornerRound(
            side=self.side,
            x=far_origin[0],
            y=far_origin[1],
            z=far_origin[2],
            u_dir=self.u_dir,
            v_dir=self.v_dir,
            n_dir=self.n_dir,
            width=self.width,
            thickness=self.thickness,
            radius=radius,
            parent=self.bend_id,
        )
        self._part.make_bend(feature)
        self._terminal = True
        return self

    def hole(self, pos: tuple[float, float], diameter: float, depth: float | None = None):
        """Drill a hole through this flange's own face.

        Args:
            pos: `(u, v)` position on the flange's face -- `u` along `u_dir` from this
                flange's fold line, `v` along `v_dir` away from it.
            diameter: Hole diameter.
            depth: Defaults to the sheet thickness (drilled through).

        Raises:
            NotImplementedError: If this flange's face isn't axis-aligned (its cumulative
                bend angle isn't a multiple of 90 degrees) -- see `_side_for_normal`.
        """
        depth = self.thickness if depth is None else depth
        centre = _offset(self.origin, (self.u_dir, pos[0]), (self.v_dir, pos[1]))
        side = _side_for_normal(self.n_dir)
        feature = FlangeHoleCut(
            side=side,
            x=centre[0],
            y=centre[1],
            z=centre[2],
            u_dir=self.u_dir,
            v_dir=self.v_dir,
            n_dir=self.n_dir,
            diameter=diameter,
            thickness=depth,
            parent=self.bend_id,
        )
        self._part.make_bend(feature)

    def rectangle(self, pos: tuple[float, float], width: float, height: float, angle: float = 0.0):
        """Cut a straight-through rectangle out of this flange's own face.

        Args:
            pos: `(u, v)` centre of the rectangle on the flange's face -- `u` along
                `u_dir`, `v` along `v_dir`, from this flange's fold line.
            width: Extent along the rectangle's own `u`-axis, before `angle` is applied.
            height: Extent along the rectangle's own `v`-axis, before `angle` is applied.
            angle: Rotation in degrees, about `pos`, within the flange's own plane.

        Raises:
            NotImplementedError: If this flange's face isn't axis-aligned -- see
                `_side_for_normal`.
        """
        centre = _offset(self.origin, (self.u_dir, pos[0]), (self.v_dir, pos[1]))
        side = _side_for_normal(self.n_dir)
        u_dir, v_dir = _rotate_in_plane(self.u_dir, self.v_dir, angle)
        feature = FlatRectangleCut(
            side=side,
            x=centre[0],
            y=centre[1],
            z=centre[2],
            u_dir=u_dir,
            v_dir=v_dir,
            n_dir=self.n_dir,
            width=width,
            height=height,
            thickness=self.thickness,
            parent=self.bend_id,
        )
        self._part.make_bend(feature)

    def polygon(self, pos: tuple[float, float], sides: int, diameter: float, angle: float = 0.0):
        """Cut a straight-through regular polygon out of this flange's own face.

        Args:
            pos: `(u, v)` centre of the polygon on the flange's face (see `rectangle`).
            sides: Number of sides, an integer > 2.
            diameter: Diameter of the polygon's circumscribed circle.
            angle: Rotation in degrees, about `pos`, within the flange's own plane. At
                `angle=0` one vertex sits at this polygon's minimum-`v_dir` point (see
                `FlatPolygonCut`) -- e.g. a 4-sided polygon needs `angle=45` to line up
                with an axis-aligned `rectangle` of the same size.

        Raises:
            NotImplementedError: If this flange's face isn't axis-aligned -- see
                `_side_for_normal`.
        """
        centre = _offset(self.origin, (self.u_dir, pos[0]), (self.v_dir, pos[1]))
        side = _side_for_normal(self.n_dir)
        u_dir, v_dir = _rotate_in_plane(self.u_dir, self.v_dir, angle)
        feature = FlatPolygonCut(
            side=side,
            x=centre[0],
            y=centre[1],
            z=centre[2],
            u_dir=u_dir,
            v_dir=v_dir,
            n_dir=self.n_dir,
            sides=sides,
            diameter=diameter,
            thickness=self.thickness,
            parent=self.bend_id,
        )
        self._part.make_bend(feature)

    def rounded_rectangle(self, pos: tuple[float, float], width: float, height: float, angle: float, radius: float):
        """Cut a rectangle with its four corners rounded to `radius`.

        Deliberately not a dedicated JSON feature: this decomposes -- in Python, at
        authoring time -- into 4 `hole()`s (one per corner) and 2 `rectangle()`s, which
        union together into a rounded rectangle. No engine needs any new geometry code for
        this shape; it rides entirely on `hole`/`rectangle` support they already have (see
        docs/content/sheetmetal-bend-design.md §4).

        Args:
            pos: `(u, v)` centre of the rectangle (see `rectangle`).
            width: Extent along the rectangle's own `u`-axis, before `angle` is applied.
            height: Extent along the rectangle's own `v`-axis, before `angle` is applied.
            angle: Rotation in degrees, about `pos`, within the flange's own plane.
            radius: Corner radius. Must be at most half of `width` and half of `height`.
        """
        if radius <= 0:
            msg = f"radius must be > 0, got {radius}."
            raise ValueError(msg)
        if 2 * radius > width or 2 * radius > height:
            msg = f"radius={radius} is too large for a {width}x{height} rounded_rectangle."
            raise ValueError(msg)

        angle_rad = math.radians(angle)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

        def _rotated(du: float, dv: float) -> tuple[float, float]:
            return (
                pos[0] + du * cos_a - dv * sin_a,
                pos[1] + du * sin_a + dv * cos_a,
            )

        half_u, half_v = width / 2 - radius, height / 2 - radius
        for du in (-half_u, half_u):
            for dv in (-half_v, half_v):
                self.hole(pos=_rotated(du, dv), diameter=2 * radius)

        self.rectangle(pos=pos, width=width, height=height - 2 * radius, angle=angle)
        self.rectangle(pos=pos, width=width - 2 * radius, height=height, angle=angle)


def _grow_part_bounds(part, origin, u_dir, v_dir, n_dir, width: float, height: float, thickness: float):
    """Grow `part`'s bounding box to include a flange's 8 corners.

    Material spans the thickness in the `-n_dir` direction from `origin`, not `+n_dir`:
    `n_dir` is the *outward* face normal (matching the base plate's own convention, where
    `n_dir=(0,0,1)` and its material sits *below* that, from `z=0` to `z=thickness`) --
    `origin` is on the outer face, the material is behind it.
    """
    xs, ys, zs = [], [], []
    for u in (0.0, width):
        for v in (0.0, height):
            for n in (0.0, -thickness):
                corner = _offset(origin, (u_dir, u), (v_dir, v), (n_dir, n))
                xs.append(corner[0])
                ys.append(corner[1])
                zs.append(corner[2])
    part.x_min, part.x_max = min(part.x_min, *xs), max(part.x_max, *xs)
    part.y_min, part.y_max = min(part.y_min, *ys), max(part.y_max, *ys)
    part.z_min, part.z_max = min(part.z_min, *zs), max(part.z_max, *zs)
    part.make_bounding_box()


def root_bend_side(cycad_side) -> BendSide:
    """Build the root `BendSide` for one of a part's own LEFT/RIGHT/FRONT/BACK sides.

    Deliberately uses `part.x_size`/`y_size`/`z_size` (fixed at construction, with the
    base plate always at the origin) rather than `part.x_min`/`x_max`/`z_max` -- those
    grow with every bend already added (`_grow_part_bounds`), so reading them here would
    make a second independent root bend (e.g. `.left` after `.front` has already grown
    `z_max`) start from the wrong place. Same class of bug flagged for whole-part
    `round_corners()` in docs/content/bending-design.md §11, caught here by actually
    building a part with bends on more than one side, not by re-reading the doc.
    """
    part = cycad_side._parent
    side = cycad_side.name
    if side not in _FLAT_DIRECTIONS:
        msg = f"Bends can only be made from LEFT, RIGHT, FRONT, or BACK, not {side}."
        raise ValueError(msg)

    flat_dir = _FLAT_DIRECTIONS[side]
    u_dir = _U_DIRECTIONS[side]
    if side == FRONT:
        origin, width = (0.0, 0.0, part.z_size), part.x_size
    elif side == BACK:
        origin, width = (0.0, part.y_size, part.z_size), part.x_size
    elif side == LEFT:
        origin, width = (0.0, 0.0, part.z_size), part.y_size
    else:  # RIGHT
        origin, width = (part.x_size, 0.0, part.z_size), part.y_size

    return BendSide(
        part,
        side=side,
        origin=origin,
        u_dir=u_dir,
        v_dir=flat_dir,
        n_dir=_Z_HAT,
        flat_dir=flat_dir,
        width=width,
        height=0.0,
        thickness=part.z_size,
        cumulative_angle=0.0,
        bend_id=None,
    )
