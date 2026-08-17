<!--
SPDX-FileCopyrightText: 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Design: Sheet Metal Bending

> **Superseded**: this doc proposed adding bending directly onto the existing `SheetMetal` part
> type. After building a prototype on that basis, we concluded `SheetMetal` is the wrong
> foundation for it — see [`sheetmetal-bend-design.md`](sheetmetal-bend-design.md) for the
> current direction (a standalone `SheetMetalBend` part type + dedicated `FreeCADBend` engine).
> Kept here for historical context only; do not implement from this doc.

Status: **Draft / RFC** — not yet implemented. This is a proposal for review, written after
reading the current codebase, the abandoned `helen_SS-180_bending` branch, and two FreeCAD
proof-of-concept scripts found on this machine
(`~/src/cycax-playpen/sheetmetal-bend/sheetmetal_part.py`,
`~/src/claude-projects/sheetmetal_part.py`). Open questions are collected at the end.

## 1. Goal

Let a `SheetMetal` part carry one or more bends (flanges), defined in Python, and have every
engine produce something reasonable from that:

- **FreeCAD**: a *real* bent solid, built with the FreeCAD SheetMetal workbench, so unfolding is
  correct. Export the unfolded flat pattern as DXF (for cutting) and the bent solid as STEP —
  with the bend lines **and their annotation** ("90° UP") already on the DXF, so nobody has to
  reopen it in FreeCAD to hand-add that text.
- **build123d / OpenSCAD**: no real bend/unfold capability, so *fake it* — generate a 3D solid
  that looks like the finished bent part (flat flange faces at the right angle), good enough for
  visualization/assembly-fit checks, not for manufacturing.
- **JSON**: one `bend` feature type, replacing the current placeholder in
  `data-file-part-spec-features.md`, expressive enough for both of the above.

Bending only ever applies to `SheetMetal` parts, and a bent part is still **one part** (one JSON
file, one growing bounding box) — not an assembly of separate flange parts. This matches how
`box_add`/`RectangleAddOn` already extends a part's own bounding box in-place
(`CycadSide._redefine_surface`, `cycad_side.py:44`), and is what the abandoned bend prototype
assumed too (`features.py` on `helen_SS-180_bending`: "*When you add a bend you need to grow the
size of the sheet metal.*").

## 2. What's already there

- `SheetMetal` (`cuboid.py:82`) is currently just a `Cuboid` with `colour="gray"` — no material,
  no bend properties, `z_size` doubles as thickness.
- The JSON spec (`data-file-spec-new.md` §Bending, `data-file-part-spec-features.md` §Bend)
  already anticipates a `bend` feature/action and explicitly leaves the schema open. A `material`
  object (`name`/`code`/`standard`) is already spec'd at the part level, unused by any real code
  yet.
- `Feature`/`CycadPart` already support most of what a bend needs structurally: per-side helper
  methods on `CycadSide` (`box`, `box_add`, `hole`, …) that compute position from the part's
  current bounding box and then call `_redefine_surface` to grow it — a 90° bend is a small
  extension of this existing pattern, not a new mechanism (new `CycadSide` method + new `Feature`
  subclass). The one thing that *isn't* already there despite being spec'd: per-feature `rotate`
  (`Order of Operations` in `data-file-spec-new.md`) is documented but not implemented anywhere
  in the engines — confirmed by grep, see §5 — so it can't be leaned on for non-90° bends without
  someone building it first.
- The FreeCAD engines (`part_freecad.py`, `cycax_part_freecad.py`, `engines/engine_freecad.py`)
  draw every feature as a plain BREP boolean (`Part.makeBox`, `.cut`, `.fuse`) — no notion of
  sheet metal at all. There's no reference to the FreeCAD SheetMetal workbench anywhere in this
  repo.
- **The FreeCAD SheetMetal workbench (by shaise) is already installed** on this machine
  (`~/.local/share/FreeCAD/Mod/sheetmetal`), and there is a **working proof of concept** for
  scripting it headlessly, in two near-identical sibling projects (not part of this repo):
  `sheetmetal_part.py` drives `SheetMetalCmd.SMBendWall` to add flanges (including
  flange-on-flange), `SheetMetalUnfoldCmd.SMUnfold` to unfold, and `importDXF.export()` on the
  unfold's generated sketches to get a DXF with outline/internal/bend layers. Confirmed
  constraint from that script: **sketch generation for unfold requires GUI mode** — fine for us,
  since `cycax_part_freecad.py` already runs FreeCAD with `FreeCADGui` available (it's launched
  as `[app_bin, script]`, not `--console`).
- **An abandoned attempt exists** on `origin/helen_SS-180_bending` (5 commits, last touched
  2026-08-07, not merged). It took a different path from the one above: no SheetMetal workbench,
  just a plain `RectangleAddOn` box for the flange (`make_bend()` in `cycad_part.py`) plus a
  hand-rolled `PartEzdxfEngine` (`ezdxf`-based) that tried to compute bend allowance itself
  (K-factor formula) and draw bend lines by hand. It's unfinished and has bugs (e.g. a
  syntax error in `build_scad`, an incomplete `circle_in_part`), but it's useful evidence of two
  things: (a) the team already independently converged on K-factor + bend radius + internal/
  external as the relevant bend-allowance inputs, and (b) doing bend-allowance math by hand in
  Python is fiddly and error-prone — one more reason to let FreeCAD's SheetMetal workbench do
  that arithmetic for the real-bend path rather than re-deriving it (see §5).
- `bend.py` (repo root) is your own sketch of two possible calling conventions; see §4.

## 3. `SheetMetal` defaults: material, k-factor, bend radius

```python
class SheetMetal(Cuboid):
    def __init__(
        self,
        part_no: str,
        x_size: float,
        y_size: float,
        z_size: float = 2.0,
        assembly: Assembly | None = None,
        material: dict | None = None,
        k_factor: float = 0.44,
        bend_radius: float | None = None,
    ):
        super().__init__(...)
        self.material = material or {"name": "mild-steel", "code": "1008", "standard": "AISI"}
        self.k_factor = k_factor
        self.bend_radius = bend_radius if bend_radius is not None else z_size  # thickness is a common minimum
```

Plus setters so these can be changed after construction, mirroring `beveled_edge()`'s style
rather than requiring re-construction:

```python
sheet.set_material(name="stainless-steel", code="304", standard="AISI")
sheet.set_bend_defaults(k_factor=0.4, bend_radius=1.5)
```

`k_factor=0.44` and `bend_radius = thickness` are the same defaults the abandoned prototype and
the FreeCAD proof-of-concept both independently landed on — reasonable to keep as the library
default rather than inventing a third number. Every individual bend can still override
`k_factor`/`radius` for that one bend (§5); the part-level values are just what a bend uses when
it doesn't specify its own.

`material` reuses the JSON spec's existing (unused) `material` object verbatim
(`data-file-spec-new.md` §Material) — no new shape.

## 4. Python authoring API

### Where the method lives

`bend()` belongs on `CycadSide`, next to `box`/`hole`/`box_add`, not as a new top-level
`CycadPart` method — bending *is* "add a box-ish thing to this side", it just also folds it and
carries bend metadata:

```python
sheet.left.bend(angle=90, height=20)
```

matches the existing idiom (`sheet.left.box_add(...)`, `sheet.left.hole(...)`) instead of adding
a parallel, differently-shaped API surface.

### Chaining onto a flange (bend.py's Option A vs Option B)

Your sketch in `bend.py` raised two options and marked B (context managers) the winner. Both
options need the same underlying thing: `bend()` must return an object that itself exposes
`.left`/`.right`/`.front`/`.back` (or a `.far` for "the distal edge of this flange, whichever
direction that is in space") so a second bend can be anchored to the *new* flange instead of the
base sheet — this is the "bend nested in a bend" case the spec already allows
(`data-file-part-spec-features.md` §Bend: "*Bends can be nested in one another*") and that the
FreeCAD proof-of-concept implements as `from: "left_wall"`.

Concretely, propose `bend()` returns a `BendSide` (a `CycadSide` subclass scoped to the new
flange's local frame, tracking which part-level feature it descends from):

```python
left_flat = sheet.left.bend(angle=45, height=100)
left_flat.left.bend(angle=90, height=60)     # Option A: plain chaining
```

Since a `with` block's `__enter__` can just `return self`, `BendSide` can support **both**
syntaxes for free — there's no teardown work to do on `__exit__` (unlike a file handle or lock,
nothing needs releasing), so `with` buys purely visual nesting of the bend hierarchy in the
source, with no different semantics from Option A:

```python
with sheet.right.bend(angle=45, height=100) as bend1:
    with bend1.bend(angle=90, height=60) as bend2:
        bend2.bend(angle=90, height=10)
```

Recommend implementing `BendSide.__enter__`/`__exit__` as this thin trivial pass-through (`bend.py`'s
own draft `__exit__` is missing the required `exc_type, exc_val, exc_tb` params — a real
implementation needs those, even if unused) so people can use whichever reads better at a given
call site, rather than picking one and blocking the other.

### `bend()` signature (draft)

```python
def bend(
    self,
    angle: float = 90.0,
    height: float = ...,          # flange length, flat, measured from the bend line
    *,
    direction: str = "up",        # "up" or "down" relative to the side's outward normal
    radius: float | None = None,  # defaults to sheet.bend_radius
    k_factor: float | None = None,  # defaults to sheet.k_factor
    gap1: float = 0.0,
    gap2: float = 0.0,
    label: str | None = None,     # DXF annotation text; auto-generated if omitted (see §5)
) -> BendSide:
```

`gap1`/`gap2` (relief at each end of the bend line, before the corner) are carried over from the
FreeCAD proof-of-concept's `SMBendWall` parameters of the same name — needed whenever two bends
meet at a corner, to avoid the flanges colliding/tearing.

## 5. JSON: the `bend` feature

Extends `data-file-part-spec-features.md` §Bend, replacing "remaining fields ... not yet
designed":

```json
{
  "name": "left_wall",
  "type": "bend",
  "action": "bend",
  "side": "left",
  "parent": null,
  "angle": 90.0,
  "height": 20.0,
  "direction": "up",
  "radius": 2.0,
  "k_factor": 0.44,
  "gap1": 0.0,
  "gap2": 0.0,
  "label": "90° UP"
}
```

- **`parent`**: `null`/absent = bend off the base sheet; otherwise the `name` of an earlier
  `bend` feature in this same part's `features` list, i.e. "bend off *that* flange, not the base
  sheet". This is what makes nested bends serializable without inventing a tree structure in the
  JSON — the list stays flat, `parent` just points backwards by name, same spirit as how
  assemblies reference parts by name.
- **`side`**: which edge of the parent (base sheet or flange) to bend from — `left`/`right`/
  `front`/`back` as usual when the parent is the base sheet. When the parent is *itself* a
  flange, `side` means "which edge of that flange's own local rectangle" — this needs a firm
  answer; see Open Questions. The FreeCAD PoC used `"end"` as a special value meaning "the edge
  furthest from the original fold"; that reads awkwardly next to `left/right/front/back` and
  is one of the things worth deciding before implementing (§Open Questions).
- **`direction`**: `up`/`down`, replacing the old prototype's `internal: bool` with a name that
  says what it does instead of which side-effect it has. **Resolved**: always relative to the
  completed part's *unfolded* state, which lies entirely in the same plane as the base
  `SheetMetal` feature — every bend ultimately originates from that one base feature, so
  picturing the whole flat pattern laid out coplanar with the base sheet gives a single,
  unambiguous reference frame regardless of nesting depth. `up`/`down` means which side of that
  one shared plane (the base feature's own normal) the flange folds toward, never relative to an
  intermediate flange's own post-fold orientation — so no per-flange local-normal tracking is
  needed at authoring time.
- **`corner_reference`**: `"outer"` (default) / `"inner"` / `"thickness_outer"` / `"offset"` (with
  an accompanying `offset` field when `"offset"` is used). Maps 1:1 to FreeCAD SheetMetal's
  `BendType` property on `SMBendWall` (`SheetMetalCmd.py:1696`, options `"Material Outside"`
  (default) / `"Material Inside"` / `"Thickness Outside"` / `"Offset"`) — verified against the
  installed workbench source, not guessed. This is the "does the part get wider, or does the
  outer size stay fixed" choice you flagged: `"outer"` keeps each wall's outer face flush with
  the corner (outer envelope matches the specified dimensions exactly); `"inner"` pulls the wall
  inward by `thickness + radius` so the *inside* faces meet cleanly instead, growing the outer
  envelope by roughly that amount at every such bend. This is independent of, and easy to
  conflate with, `height`'s own convention below — `corner_reference` is about where the corner
  sits, `height`/`length_spec` is about where *along* the flange the specified length is
  measured to. Applies even to a single, non-nested bend (not just where two bends meet at a
  corner) — it's an offset applied to that one bend's own attach point. For the fake renderers
  (§7) this only ever changes a *position* offset on the box (by `0` or `thickness + radius`
  along the fold axis), never a rotation — so it doesn't push non-90° bends into the "needs real
  rotation" bucket, it's compatible with the 90°-only MVP phase too.
- **`radius`**, **`k_factor`**: per-bend overrides of the `SheetMetal` defaults (§3). Always
  written out explicitly in the JSON (per the spec's "verbose by design" principle) even when
  they equal the part's default — an engine reading one `bend` feature shouldn't need to also
  read the part-level `material`/`k_factor` to know how to build it.
- **`label`**: the DXF annotation text. Auto-generated as `f"{angle:g}° {direction.upper()}"` →
  `"90° UP"` when not explicitly set — directly automating the manual step described in your
  prompt ("*add '90deg up'*"). Always present in the exported JSON (never computed at
  render-time from `angle`/`direction`), so any engine can place it verbatim without
  re-implementing the formatting rule.
- **`x`/`y`/`z`/`x_size`/`y_size`/`z_size`**: still present per the [common
  fields](data-file-part-spec-features.md#common-fields), describing the flange as an
  axis-aligned box. For a 90° bend this is exactly the existing `box_add`/`RectangleAddOn` trick
  (swap which dimension becomes "thickness" depending on `side` — no rotation transform needed,
  see §7). For any other angle an axis-aligned box can't represent a tilted flange at all — see
  the `rotate` caveat immediately below.
- **`rotate`** is listed as a "common field" in `data-file-spec-new.md`, but **it is currently
  unimplemented**: no `Feature` subclass sets it, and no engine decoder (`part_build123d.py`,
  the OpenSCAD engines, `cycax_part_freecad.py`) reads a `rotate` key off a feature — verified by
  grep, not just by reading the spec. Only whole-*part* rotation exists today
  (`CycadPart.rotate_freeze_*`/`self.rotation`, a different mechanism). So a non-90° `bend`
  feature is blocked on *someone* adding real per-feature rotation support somewhere — this is a
  real dependency this design introduces, not a detail to gloss over. See §7 for where that
  lands.
- **`action`**: `"bend"`, not `"add"` — this is the signal that tells the FreeCAD engine "don't
  boolean-fuse this, do a real `SMBendWall`", while still letting the fallback renderers ignore
  `action` and just use the geometry fields.

## 6. FreeCAD engine: real bending

Both `cycax_part_freecad.py` and `engines/cycax_part_freecad.py` gain a `bend` case in their
feature dispatch (`build()`'s `match`/`if` chain), parallel to the existing `beveled_edge`
handling — it also mutates `solid` rather than fitting the uniform add/cut pattern, so it's
already precedented.

Key implementation difference from the sibling proof-of-concept: that script *finds* edges by
searching the shape's `BoundBox` geometry after the fact
(`get_edge_for_base_side`/`get_edge_for_flange`). We don't need to — cycax already knows the
exact fold-line coordinates and which feature is whose `parent`, because that's exactly what
`x`/`y`/`z`/`side`/`parent` in the JSON encode. So instead of guessing, keep a small
`name -> (FreeCAD object, fold-line edge)` map as features are processed in order (mirroring the
proof-of-concept's `bend_objects` dict), and look up the parent by name directly. Steps per
`bend` feature:

1. Look up the parent solid (`solid` itself if `parent` is null, else `bend_objects[parent]`).
2. Compute the fold-line edge from the *known* geometry (`x`/`y`/`z`/side of the feature, already
   in the part's own coordinate frame) rather than re-deriving it from a bounding-box scan.
3. Call `SheetMetalCmd.SMBendWall(obj, parent_solid, [edge_name])`, then set
   `.radius`/`.angle`/`.length`/`.kfactor`/`.gap1`/`.gap2`/`.invert` from the feature's fields,
   plus `.BendType` from `corner_reference` and `.LengthSpec` from `length_spec` (both §5,
   passed straight through — cycax's values are named 1:1 with FreeCAD's own, so this is a
   direct assignment, not a translation table). Let SheetMetal's own bend-allowance math do the
   developed-length calculation — don't reimplement the K-factor formula in cycax (unlike the
   abandoned `helen_SS-180_bending` branch, which tried to and left it half-finished; see §2).
4. Store the new object in `bend_objects[feature["name"]]` for any child bend to reference.
5. After all features: call `SheetMetalUnfoldCmd.SMUnfold` on the final solid's base face,
   with `GenerateSketch=True`, `SeparateSketchLayers=True` (as the proof-of-concept does), then
   `importDXF.export()` the resulting sketches for the flat-pattern DXF, alongside the existing
   `render_to_stl`/`.exportStep` for the bent 3D solid.
6. **Bend annotation** — post-process the exported DXF with `ezdxf` (new dependency; the
   abandoned prototype already depended on it for a similar reason) to add a `TEXT` entity at
   each bend line's midpoint using that feature's `label`. Do this as a separate small pass over
   the DXF cycax just wrote, using the `label`/midpoint cycax already has in Python — not by
   trying to get FreeCAD to draw annotated text itself (`FreeCADGui`/`Draft` text objects are
   more awkward to script headlessly than adding a `TEXT` entity to an already-exported DXF).

If no `bend` feature is present, this whole path is skipped and a `SheetMetal` part builds
exactly like it does today (plain box) — bending only changes behavior when a part actually has
one.

## 7. build123d / OpenSCAD: faking it

**Correction to an earlier draft of this section**: it originally claimed "I didn't find
sheet-metal-specific functionality in build123d" — that was wrong, caught only once asked to go
look properly. build123d **does** ship a real primitive for this:
`build123d.make_brake_formed()` (`operations_part.py:268`, exported from `build123d/__init__.py`,
registered as a `BuildPart`-context op in `build_common.py` — present in `0.9.1`, the version
this repo already depends on and has installed, per `.hatch/cycax/.../build123d/_version.py`).

```python
make_brake_formed(
    thickness: float,
    station_widths: float | Iterable[float],
    line: Edge | Wire | Curve | None = None,
    side: Side = Side.LEFT,      # Side.LEFT/RIGHT/BOTH — which way to offset the material
    kind: Kind = Kind.ARC,       # Kind.ARC/INTERSECTION/TANGENT — corner transition style
    clean: bool = True,
    mode: Mode = Mode.ADD,
) -> Part
```

Docstring: *"Create a part typically formed with a sheet metal brake from a single outline. The
line parameter describes how the material is to be bent."* Concretely: give it a 2D polyline
(`line`) whose vertices are the fold points, a `thickness`, and a width per vertex
(`station_widths`); it offsets the line by `thickness` (rounding each corner per `kind` —
`Kind.ARC` gives a filleted bend transition), extrudes each resulting segment to its
station width, and sweeps/fuses the sections together into one solid. This is exactly a
press-brake sequence of folds along one straight run — precisely the shape of one of cycax's
bend *chains* (a base edge plus every bend nested off it via `parent`, §5), and it handles
**arbitrary bend angles natively**, because the angle is just however sharply the input polyline
turns at that vertex — no rotation math needed in cycax's own decoder at all.

Revised plan for `part_build123d.py`: for each distinct bend chain on a `SheetMetal` part (i.e.
each base edge that has at least one `bend` feature anchored to it, directly or via `parent`),
build the 2D polyline that walks from the base edge through every bend in that chain (segment
length = each `height`, turn angle at each vertex = `180° - angle`, turn direction = `up`/`down`
per §5's now-fixed unfolded-plane convention) and call `make_brake_formed` once for that chain,
with `station_widths` set to the sheet's other in-plane dimension. Fuse the result with the base
plate `Box` and with every other chain's solid (a tray with bends on more than one side has one
`make_brake_formed` call per bent side, not one call for the whole part — the function models a
single connected run, not a branching or multi-directional one). This replaces the
per-feature-as-a-box plan for build123d specifically, and **removes the dependency on generic
per-feature `rotate` for build123d's bend rendering** — the earlier decision to build `rotate`
now (§10) can stand on its own merits for other feature types, it's just no longer *required* by
non-90° bends in this engine. It also gives a rounded bend transition essentially for free
(`Kind.ARC`) rather than the sharp corner the box-based plan settled for, though the fillet size
is tied to `thickness` itself, not independently to the bend's own `radius` field — a real but
minor fidelity gap worth knowing about (it doesn't affect footprint/length the way FreeCAD's
actual bend-allowance math does; it's a rendering-only rounding).

**OpenSCAD has no equivalent** — no native brake-forming/sheet-metal function and no sheet-metal
library worth pulling in (its CSG model has no concept of a bend to integrate with). So OpenSCAD
keeps the original plan: reuse the cuboid decoder outright for 90° bends (no rotation needed,
same `box_add`-style dimension swap `helen_SS-180_bending`'s abandoned `make_bend()` already
proved out), and needs real rotation support (`rotate([...])`, native to OpenSCAD) for non-90°
bends — this is the one place the generic per-feature `rotate` (§5) is still a hard requirement,
not just a nice-to-have.

**Wider context worth knowing**: build123d has a full "Sheet Metal Tools" item on its public
roadmap ("dedicated tools and operators for sheet metal design and unfolding... bends, hems,
flanges, tabs, and reliefs... unfolding logic... K-factor or bend allowance model... DXF/SVG flat
pattern export" — [gumyr/build123d#305](https://github.com/gumyr/build123d/issues/305)). If that
ever ships, build123d could become a second *real* (not fake) bend engine, not just a
visualization fallback. It's not close, though: filed August 2023, no assignee, no branch or PR,
explicitly not gating the 1.0.0 milestone, and the one comment on it flags an unresolved
technical blocker (`OCP`'s face-continuity detection behaving inconsistently). Nothing to design
around right now — `make_brake_formed` (already shipped, already installed) is what to build
against; the fuller roadmap item is a "watch for later," not a dependency.

## 8. Testing

Follow the existing pattern in `tests/test_bevel.py` — build a `SheetMetal` part with one or more
bends, `save()`, `render()` on each engine, and compare outputs against checked-in reference
fixtures (`check_stl_reference`, `hex_code_check` for the `.scad`/JSON hash, `check_json_reference`
for the exported part JSON). Suggest covering, incrementally:

1. A single 90° bend on one side (base case) — JSON export shape, then each engine.
2. A bend with a non-90° angle, and one with `direction="down"`.
3. Two independent bends on different sides of the base sheet (no nesting).
4. A nested bend (`parent` pointing at another bend) — the case none of the fallback engines
   need to understand specially, but FreeCAD's edge-lookup-by-name does.
5. FreeCAD-specific: assert the exported DXF contains the expected `TEXT` entity/value at
   roughly the bend line's midpoint, and that the unfolded flat-pattern bounding box matches a
   hand-computed expected size for at least one non-90° case (a real check that bend-allowance
   came out right, not just "a DXF was produced").

FreeCAD/SheetMetal-workbench tests will need whatever the existing FreeCAD tests already do to
be optional/skippable in CI environments without an AppImage + workbench installed — check how
`test_assembly_freecad.py` currently gates that, and give the new tests the same gate rather than
inventing a new one.

## 9. Suggested phasing

1. `SheetMetal` material/k-factor/bend-radius fields + setters (§3) — no behavior change yet,
   just data.
2. `bend` JSON feature + `CycadSide.bend()`/`BendSide` (§4–5), single bend off the base sheet
   only (`parent` always null) — gets the data model and JSON export solid before tackling
   nesting.
3. build123d fake rendering via `make_brake_formed` per bend chain (§7) — handles arbitrary
   angles from the start, no rotation dependency; gives visual feedback on (2) while FreeCAD
   support is still being built. OpenSCAD fake rendering, **90° only** for now (§7) — cheap,
   reuses the existing cuboid decoder as-is.
4. FreeCAD real bending, single bend (§6, steps 1–5, no `bend_objects` chaining needed yet). Not
   blocked on (3) or on per-feature `rotate` — SheetMetal handles arbitrary angles natively.
5. Bend annotation on the DXF (§6 step 6).
6. Nested bends (`parent` pointing at another bend) — Python chaining API (§4) +
   `bend_objects`-by-name lookup in the FreeCAD engine (§6), plus per-chain grouping in the
   build123d decoder (§7).
7. Non-90° fake rendering in OpenSCAD only (§7) — needs real per-feature rotation
   (`rotate([...])`) added to that decoder; can land whenever, doesn't block anything else since
   FreeCAD (dimensionally-correct) and build123d (via `make_brake_formed`) don't need it.

Each phase is independently mergeable and testable; nothing later blocks something earlier from
shipping.

## 10. Decisions (resolved 2026-08-15)

All open questions from the original draft are now resolved:

1. **`side` on a flange-of-a-flange**: reuse `left`/`right`/`front`/`back` in the flange's own
   local frame, allowed on any of its four edges (not restricted to just the far edge) —
   matching the FreeCAD PoC's generality.
2. **`length_spec` convention**: maps to FreeCAD SheetMetal's `LengthSpec` property, default
   `"leg"` (the flat straight-leg length, excluding the curved bend region) — proposed and not
   objected to; treat as confirmed. Independent of `corner_reference`/`BendType` (§5).
3. **`direction="up"/"down"`**: always relative to the completed part's *unfolded* state, which
   lies in the same plane as the base `SheetMetal` feature — a single, unambiguous reference
   frame regardless of nesting depth. See §5 for the full rationale.
4. **Corner handling**: `gap1`/`gap2` is enough; no dedicated corner-relief/corner-cut feature
   needed.
5. **Bend syntax**: support both plain chaining and `with`-blocks (§4).
6. **Default `material`**: `mild-steel` confirmed as the right default (§3's `1008`/`AISI` detail
   not specifically revisited, but the family choice is confirmed).
7. **ezdxf**: approved as a new dependency (§6 step 6).
8. **Per-feature `rotate`**: build it now, not deferred (§5, §7).
9. **`corner_reference`/`BendType` default** (added after the original list, §5): proposed
   `"outer"`, matching FreeCAD's own default — naming confirmed correct, default value not
   separately objected to; treat as confirmed pending anything that turns up once FreeCAD is
   next open to double-check against.

Nothing blocking remains — implementation can proceed per the phasing in §9.

## 11. Corner rounding/beveling

Raised after the doc was otherwise settled: sheet metal corners are routinely rounded/chamfered
today by hand, back in FreeCAD, after cycax produces the part. Two scopes were described, both
wanting the *same* underlying primitive:

1. **Whole-part**: round (or chamfer) the sharp vertical corners of the base sheet's footprint.
2. **Per-flange**: round the two far corners of a flange, but only a *terminal* one (no further
   bend allowed on it afterward, since a subsequent bend needs that corner's material).

### No new primitive needed

`CycadPart.beveled_edge(edge_type, side1, side2, size)` (`cycad_part.py:655`) already does
exactly this geometry — it rounds or chamfers the edge where two adjacent sides meet, including
the *vertical* edges at a flat plate's four corners (`test_bevel.py` already exercises e.g.
`side1="LEFT", side2="FRONT"`, one of those four). So "how will the terminology work" has a short
answer: it already exists, `edge_type="round"`/`"chamfer"` — no new `Feature` subclass, no new
JSON `type`. What's missing is just a convenient way to *call* it at each of these two scopes,
plus one real geometric wrinkle (below) that the naive version gets wrong.

Proposed sugar, both scopes sharing one name and both requested as worth having:

```python
sheet.round_corners(radius=3)                      # whole-part, "a setting/method" — see below
sheet.round_corners(radius=3, edge_type="chamfer")  # same, chamfered instead of rounded

flange = sheet.left.bend(angle=90, height=20)
flange.round_corners(radius=3)                      # per-flange — marks the flange terminal
```

Each is sugar over 4, resp. 1, calls to the existing `beveled_edge()` — not new geometry, just a
new entry point plus (for the flange case) enforcement of the "no bend after this" rule.

**Both entry points, since both were asked for**: `round_corners()` as a plain method (callable
whenever — "a method call at the end"), *and* as a `SheetMetal.__init__(..., corner_radius=None,
corner_edge_type="round")` kwarg applied automatically at construction ("a setting at the
beginning"). The kwarg path is just `round_corners()` called once at the end of `__init__` when
`corner_radius` is given — one implementation either way.

### The real wrinkle: base footprint vs. the live, bend-grown bounding box

`beveled_edge()` reads `self.bounding_box[side]` — the part's *current* bounding box. But that
box grows every time a bend extends a side (`CycadSide._redefine_surface`, the same mechanism
`box_add`/`bend()` use, §4/§7). So "round the 4 corners of the current bounding box," called
after any bend exists, would round a corner out on a flange's far edge instead of the original
base plate's corner — silently wrong, not an error.

Fix: whole-part `round_corners()` must work against the base plate's *original* footprint
(`x_size`/`y_size` as given to `SheetMetal.__init__`), tracked separately from the live
bend-grown bounding box — not derived from `self.bounding_box` the way `beveled_edge()` currently
reads it directly. Following on from that: a corner where either adjacent side already has a
bend isn't an exposed corner anymore (it's the fold line into a flange), so whole-part
`round_corners()` should skip it — that corner's rounding is what the *per-flange* call handles
instead, on the flange itself.

The per-flange case doesn't have this problem: a `BendSide`'s own local corner coordinates are
exactly what its chaining logic already computes (§4), not the part's overall bounding box.

### Per-flange terminal constraint

```python
def bend(self, ...):
    if self._corners_rounded:
        msg = "Cannot bend a flange whose corners have already been rounded."
        raise ValueError(msg)
    ...

def round_corners(self, radius, edge_type="round"):
    self._corners_rounded = True
    ...  # beveled_edge() in this flange's local frame
```

Matches the existing style of raising a clear `ValueError` for a structurally-invalid call
(`beveled_edge()` itself already does this for same-axis side pairs).

### Engine impact: none expected

`decode_beveled_edge` (FreeCAD, `cycax_part_freecad.py`) and `_decode_beveled_edge` (build123d,
`part_build123d.py`) are both generic BREP boolean cuts against whatever solid already exists —
neither cares whether that solid came from a plain box, an `SMBendWall` chain (§6), or a
`make_brake_formed` sweep (§7). Once the coordinate fix above is in place, no per-engine
decoder changes are expected for this feature — it's authoring-API and coordinate-math work,
reusing an existing rendering path everywhere.

### Left for whenever this is picked up

- Default `radius`/`edge_type` for the sugar methods — no strong reason not to require `radius`
  explicitly (like `beveled_edge()` does today) and default `edge_type="round"` given "so they
  are not sharp" was the framing; flag if a different default is wanted.
- Whether whole-part `round_corners()` should be an error or a silent no-op when called with no
  un-bent sides left to round (i.e. every side already has a bend) — an edge case, not a
  blocker.
