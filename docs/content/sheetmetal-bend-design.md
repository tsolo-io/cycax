<!--
SPDX-FileCopyrightText: 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Design: `SheetMetalBend`

Status: **Draft / RFC** — supersedes the bend-related parts of `bending-design.md`. That
earlier doc proposed adding bending directly onto the existing `SheetMetal` part type; after
building a working prototype on top of it, we concluded `SheetMetal` (currently just a `Cuboid`
shared with `Print3D`, distinguished by name only) is the wrong foundation for a part whose
geometry, cut rules, and manufacturing process are fundamentally different. This doc describes a
fresh, standalone part type instead. `SheetMetal` itself is left exactly as it is — it's used
elsewhere already.

## 1. Goal and scope

CyCAx automates the production of parts that are tedious but easy to *describe* — same shape,
different sizes/hole patterns/materials, over and over. `SheetMetalBend` is that automation
surface for laser-cut, bent sheet-metal parts specifically. It is **not** trying to be a general
sheet-metal CAD tool: if a part needs a strategy this model doesn't cover, the answer is to open
FreeCAD directly, not to stretch this API to fit.

Manufacturing assumption baked into the whole design: parts are **laser cut then bent**, not
CNC'd. That means:

- Every cutout is a straight-through 2D shape (rectangle, rounded rectangle, circle, regular
  polygon) — never a 3D pocket, counterbore, or angled cut.
- Cuts are made on the flat pattern before bending, so — geometrically — a cut on a flange is just
  a 2D shape in that flange's own local plane, the same as a cut on the base sheet.
- One `bend_radius` applies to every bend in the part (no per-bend override).

Two consumers of the output matter equally: **automated generation** (scripts producing many part
variants) and **hand-typing a one-off part**. Both are exercised by the worked examples in §6.

## 2. The part: `SheetMetalBend`

Always starts as a flat rectangular sheet on the XY plane (mirrors how the FreeCAD prototype
started from `Part -> Cube`): thickness (`z_size`) is smaller than `x_size`/`y_size`; `x_size` and
`y_size` may be equal.

```python
tray = SheetMetalBend(
    part_no="aluminium_tray",
    x_size=440.0, y_size=89.0, z_size=2.0,
    material={"name": "aluminium", "code": "5052-H32", "standard": "AISI"},
    k_factor=0.42,
    bend_radius=2.0,
)
```

`k_factor` and `bend_radius` default the same way `SheetMetal` does today (`bend_radius` falls
back to `z_size` if not given) — no new defaulting rule needed, just moved onto the new type.

## 3. Bending: chained flanges

Unchanged from what's already working in `bend.py`: `.bend()` on a side returns a flange handle
(`BendSide`) that itself exposes `.far`/`.bend()`, so a bend-on-a-bend is just chaining:

```python
# Bend on a bend: wall, then a return lip folded back on the wall's far edge.
front_wall = tray.front.bend(angle=90, height=200.0)              # direction defaults to "up"
front_lip = front_wall.far.bend(angle=90, height=10.0, direction="down")
```

`direction` defaults to `"up"`; a negative angle flips it (`angle=-90` == `angle=90,
direction="down"`), matching the earlier angle/direction resolution work and its unit tests.

## 4. Cutouts: on the base sheet or on any flange

Since every cut is a straight-through 2D shape, one small family of methods covers all of them,
available on the base sheet's faces (`.top`/`.bottom`) and on any flange handle. All share the
same `pos=(x, y)` (in that face's own local plane) and, where rotation is meaningful, the same
`angle=0.0` (degrees) convention:

```python
flange.hole(pos=(30.0, 30.0), diameter=13.0)
flange.rectangle(pos=(20.0, 10.0), width=30.0, height=15.0, angle=15.0)
flange.rounded_rectangle(pos=(20.0, 10.0), width=10.0, height=10.0, angle=0.0, radius=3.0)
flange.polygon(pos=(20.0, 10.0), sides=6, diameter=14.0, angle=0.0)
```

- `hole` is the existing circle-cut shortcut — unchanged, no `angle` (a circle has no orientation).
- `rounded_rectangle` is **not** its own JSON feature. It's a thin Python-layer helper that emits
  six existing primitives: 4 `hole`s (diameter `2*radius`, centred `radius` in from each corner)
  plus 2 `rectangle`s (`width x (height - 2*radius)` and `(width - 2*radius) x height`), which
  union together into a rounded rectangle. This is a deliberate choice — it means no engine
  (FreeCAD, build123d, OpenSCAD) needs any new geometry code at all for `rounded_rectangle`; it
  rides entirely on `hole`/`rectangle` support they already need. The JSON output shows 6 plain
  cutouts, not a semantic "rounded rectangle" feature — traded away on purpose to keep the engines
  simple.
- `polygon` is sized by **`diameter`** of its circumscribed circle, and — matching the existing
  `regular_polygon` JSON feature already documented in `data-file-part-spec-features.md` — has one
  vertex at its minimum-`y` point before `angle` is applied. This means a 4-sided `polygon` and a
  same-size `rectangle` are 45° apart unless the polygon is rotated to match; that's expected, not
  a bug, and worth knowing when hand-typing a part.
- `rectangle` keeps `angle` deliberately (needed for diagonal slots/cuts, not just axis-aligned
  ones).
- A `cut_` prefix on these names (`cut_hole`, `cut_rectangle`, ...) is still being considered but
  isn't load-bearing — trivial to rename later.

## 5. Corner rounding

Rounding a *specific* corner to a set radius is a hard requirement; rounding *every* corner of the
part to one radius is a nice-to-have, not required. The existing mechanism already covers the hard
requirement without new API: `round_corners(radius=...)` is called on the specific flange whose
far-end corners should be rounded —

```python
left_tip.round_corners(radius=6.0)
right_tip.round_corners(radius=6.0)
```

— so "which corners" is expressed by "which flange you call it on", not by a separate corner
selector.

## 6. Worked examples (ergonomics check)

Two short examples specifically to sanity-check that the calling style holds up for both a
scripted/automated caller and someone hand-typing a part.

**Bend-on-a-bend, with a hole cut into the resulting flange:**

```python
bracket = SheetMetalBend(part_no="bracket", x_size=80.0, y_size=50.0, z_size=3.0, k_factor=0.40)

# Central hole in the base sheet.
bracket.top.hole(pos=(40.0, 25.0), diameter=30.0)

# First bend off the front edge...
side_wall = bracket.front.bend(angle=90, height=60.0)
# ...then a second bend off that wall's far edge -- a bend on a bend.
grip = side_wall.far.bend(angle=45, height=20.0)

# Cutouts on the flange produced by the first bend, after it's been folded.
side_wall.hole(pos=(30.0, 30.0), diameter=13.0)                       # M12 clearance
side_wall.rectangle(pos=(15.0, 45.0), width=20.0, height=6.0, angle=30.0)
```

**A part built entirely from chained bends plus mixed cutout shapes (the kind of variant sweep
this is meant to automate — e.g. looping over a list of hole positions/tab widths to generate a
family of parts from one script):**

```python
for tab_width in (20.0, 25.0, 30.0):
    tray = SheetMetalBend(part_no=f"tray_{tab_width:g}", x_size=440.0, y_size=89.0, z_size=2.0,
                           k_factor=0.42, bend_radius=2.0)
    left_wall = tray.left.bend(angle=90, height=200.0)
    left_tip = left_wall.far.bend(angle=90, height=tab_width, direction="down")
    left_tip.round_corners(radius=6.0)
    left_tip.rounded_rectangle(pos=(10.0, 5.0), width=12.0, height=8.0, angle=0.0, radius=2.0)
```

Both read the same whether they're a one-off hand-typed part or the body of a loop generating many
variants — no different code path for "automated" vs "manual" use.

## 7. The `FreeCADBend` engine

A dedicated engine, separate from the existing `PartEngineFreeCAD`/`EngineFreeCAD` (which keep
serving `SheetMetal`/`Print3D`/`Cuboid` unchanged). Reuses the working mechanics already built and
debugged for the `SheetMetal` prototype (edge-finding by shape rather than exact idealized
coordinates, gap1/gap2 handling, the dual-candidate invert-direction scoring, the `os._exit(0)`
fix for the automation-blocking save prompt) — those parts don't change, only what they're wired
into does.

The key behavioural difference from the prototype: **keep the whole FreeCAD object tree live and
recomputable**, rather than deleting intermediate objects after building. This was a real,
deliberate change in direction — the prototype's cleanup step turned out to be cargo-culted from
an early example, not something the STEP export actually needed. Concretely:

- Base sheet: one `Part::Box` on the XY plane.
- Each bend: one `SMBendWall` object, kept in the tree (not removed).
- Each cutout and corner-round: a native, recomputable FreeCAD feature object downstream of the
  bend it belongs to — not a boolean baked onto a final flattened shape. Editing an earlier bend's
  angle in the FreeCAD GUI should re-flow through every cut/round that follows it.
- Exports read whichever object is currently the end of the chain at export time; they don't
  require deleting or hiding anything upstream.

### Outputs

For every `SheetMetalBend` part, `FreeCADBend` produces:

1. **STEP** — the folded (bent) solid.
2. **FCStd** — the live, editable FreeCAD-SheetMetal object tree (bends, cuts, and corner-rounds
   all present as real objects), so the part can be opened and hand-adjusted in FreeCAD if needed.
3. **STEP** — the unfolded (flat) pattern.
4. **DXF** — the unfolded (flat) pattern, via `SheetMetalUnfoldCmd.SMUnfold` + `importDXF.export`
   on the resulting sketches (outline/internal/bend-line layers) — the mechanism already validated
   in the `sheetmetal_part.py` proof-of-concept. This is the file that actually goes to the
   manufacturer, so it's a hard requirement, not a nice-to-have.

### Not yet decided / follow-ups

- Whether `build123d`'s fake-render path should use `make_brake_formed()` for rounded bend
  transitions instead of the current sharp-cornered oriented-box approach — a visual-fidelity
  nice-to-have, not correctness-blocking (`build123d` is explicitly the fake/visualization path;
  FreeCAD is the manufacturing-accurate one). Parked until asked for.
- OpenSCAD's fake-render path is last in the agreed build order and untouched by this pivot.
- `round_corners()` rounding *every* corner of a flange automatically (vs. the currently-supported
  "the two far corners of this specific flange") remains a nice-to-have, not required.
