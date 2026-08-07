<!--
SPDX-FileCopyrightText: 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Part Feature Specification: V2

A list of features and the fields they contain. See
[`data-file-spec-new.md`](data-file-spec-new.md) for the overall Assembly/Part JSON structure,
field units, and the [Order of Operations](data-file-spec-new.md#order-of-operations) that
governs how these fields combine.

## Common Fields

These fields apply to every feature, regardless of `type`. Each shape's section below lists
only the fields it adds on top of these.

**Fields:**

- **name**: Identifier for the feature.
- **type**: The kind of feature, e.g. `cuboid`, `cylinder`, `sphere`, `cone`,
  `regular_polygon`, `nut_cutout` (superseded by `regular_polygon` in the new format),
  `beveled_edge`, `sketch`, `bend`. Determines which additional fields apply.
- **action**: `add`, `subtract`, or `bend`.
- **side**: The reference side of the part the feature is applied to. One of `left`, `right`,
  `top`, `bottom`, `front`, `back`.
- **x** / **y** / **z**: Coordinate position of the feature, in millimetres. Applied after
  `rotate`.
- **x_size** / **y_size** / **z_size**: Dimensions of the feature, in millimetres. Only used by
  feature types with box-like dimensions (e.g. `cuboid`); other shapes use their own size
  fields (e.g. `diameter`) and only reuse `z_size` where noted below.
- **center**: Boolean. If `true`, `x`/`y`/`z` is the center point of the feature rather than
  its origin corner. Default `false`.
- **rotate** (optional): Tilts the feature's own geometry before it is positioned and combined
  with the part. A list of `{axis, angle}` entries, `angle` in degrees. Default: no rotation.

> The current implementation (`src/cycax/cycad/features.py`, `beveled_edge.py`) does not yet
> use this `type`/`action` split — today the shape name is stored under `name` (`cube`,
> `cylinder_feature`, `hole`, `sphere`, `nut`, `beveled_edge`) and the add/subtract distinction
> is stored under `type` (`"add"` / `"cut"`). The sections below describe each shape using the
> field names it will need once the engines are updated to this spec, and note the current
> code's field names where they differ.

## Existing Features

These shapes are implemented today, as `Feature` subclasses in
`src/cycax/cycad/features.py` (plus `BeveledEdge` in `beveled_edge.py`).

### Cuboid

A rectangular box feature. Implemented today by `RectangleCutOut` (`action: subtract`) and
`RectangleAddOn` (`action: add`) — both currently serialize `name: "cube"`.

**Fields:**

Uses only the [common fields](#common-fields) — `x_size`/`y_size`/`z_size` give its dimensions.
No additional fields.

### Cylinder

A cylindrical feature. Implemented today by two classes that this spec unifies into one shape
distinguished by `action`: `Cylinder` (`action: add`, currently serialized as `name:
"cylinder_feature"`) and `Holes` (`action: subtract`, currently serialized as `name: "hole"`).
A hole (e.g. for a screw or dowel) is simply a cylinder with `action: subtract`.

**Fields:**

- **diameter**: Diameter of the cylinder, in millimetres.
- **z_size**: Height of the cylinder, in millimetres (reuses the [common
  field](#common-fields); currently called `depth` in code). `x_size`/`y_size` are not used.

### Sphere

A spherical feature. Implemented today by the `Sphere` class (`action: add` or `subtract`,
currently serialized as `name: "sphere"`).

**Fields:**

- **diameter**: Diameter of the sphere, in millimetres.
- **center**: A `true` value is the most practical — a sphere's `x`/`y`/`z` is most naturally
  its center point rather than a corner.

`x_size`/`y_size`/`z_size` are not used, only `diameter`.

### Nut Cutout

!!! info

    To be replaced by the general [Regular Polygon](#regular-polygon) feature.

A cutout shaped to hold a hex nut, so it can be embedded in a (typically 3D-printed) part.
Implemented today by the `NutCutOut` class (always `action: subtract`, currently serialized as
`name: "nut"`).

**Fields:**

- **nut_type**: Which nut specification to use, e.g. `"M3"`, `"M3ISO"`, `"M6ISO"`. Each type
  maps to a fixed `diameter`/`thickness`/`side_to_side` internally.
- **depth** (optional): Depth of the cutout, in millimetres. Defaults to the nut's thickness if
  omitted.
- **vertical**: Boolean. If `false`, the nut sits with its flat side down. Default `true`.

In the new format, `nut_cutout` is superseded by the general [Regular
Polygon](#regular-polygon) feature — a hex nut cutout is just a 6-sided regular polygon sized
to the nut.

### Beveled Edge

Rounds or chamfers an edge of the part, rather than adding/subtracting a shape at a position.
Implemented by the `BeveledEdge` class (always `action: subtract`, currently serialized
as `name: "beveled_edge"`), created via `CycadPart.beveled_edge()` rather than authored
directly like the other features above.

**Fields:**

- **edge_type**: `"round"` or `"chamfer"`.
- **side1** / **side2**: The two (different, non-parallel) sides of the part that meet at the
  edge being rounded or chamfered.
- **size**: Radius of the round, or length of the chamfer, in millimetres.

`axis1`/`axis2`/`bound1`/`bound2`/`side`/`depth` are derived automatically from `side1`/`side2`
and the part's bounding box — they are not supplied directly by the caller.

## Proposed Features

These shapes are not yet implemented in code; they're design targets for this spec.

### Cone

A conical feature. Useful for e.g. countersunk holes or tapered pegs.

**Fields:**

- **diameter**: Diameter at the base of the cone, in millimetres.
- **top_diameter**: Diameter at the top of the cone, in millimetres. `0` produces a point (a
  true cone); a nonzero value produces a frustum.
- **z_size**: Height of the cone, in millimetres (reuses the [common field](#common-fields)).

### Regular Polygon

A constrained regular polygon (all sides and angles equal), extruded to a height. Replaces
[Nut Cutout](#nut-cutout) in the new format — e.g. a hex nut cutout is `sides: 6` with
`diameter` set to the nut's circumscribed-circle size.

**Fields:**

- **sides**: Number of sides, an integer `> 2`.
- **diameter**: Diameter of the polygon's circumscribed circle (the circle passing through
  every vertex), in millimetres — chosen over a side-length field so the size is independent
  of `sides`.
- **z_size**: Height to extrude the polygon along its local Z axis, in millimetres (reuses the
  [common field](#common-fields)).
- **x**/**y**/**z**: The center of the polygon (reuses the [common fields](#common-fields));
  `center` is implicitly `true` for this shape.

`x_size`/`y_size` are not used. Before `rotate` is applied, the polygon has a fixed starting
orientation on its local XY plane: one vertex sits at the polygon's minimum-`y` point (pointing
in the `-y` direction). This gives every regular polygon a consistent, repeatable shape prior
to rotation, regardless of `sides`.

### Sketch

A feature whose geometry is a 2D profile extruded ("padded") into a solid, rather than a fixed
primitive shape.

**Fields:**

- **sketch**: Array of 2D points (`{"x": ..., "y": ...}`, in millimetres) describing a closed
  polygon on the feature's local XY plane.
- **z_size**: Height to extrude the sketch along its local Z axis, in millimetres.

`x_size`/`y_size` are not used — the sketch's own points and `z_size` define its size.

### Bend

Adds a flange to the part. The flange is bent up or down at a specific degree.
The flange is the same thickness as the part's base.
Bends can only follow a cuboid base, or a bend that has already been applied to the part but the second bend must be applied to another side of the part.
Bends can be nested in one another, so multiple bends can be applied to a single part.

**Fields:**

- **side**: Should always be **left**, **right**, **front**, or **back**.

Remaining fields (fold line/axis, angle, radius, direction) are not yet designed — see
[Bending](data-file-spec-new.md#bending) and [Open
Questions](data-file-spec-new.md#open-questions).
