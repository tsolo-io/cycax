# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Sheet-metal bending: worked example, not yet backed by an implementation.

Status: DRAFT SYNTAX ONLY. This is `cycax` as a *Python interface to CAD systems* first --
this file exists purely to show what authoring a bent part should look like, before any
engine work starts. It will keep changing as implementation reveals what actually fits
cycax's existing style; nothing here is committed. See docs/content/bending-design.md for
the design this implements, and `resolve_bend_angle()` in
`src/cycax/cycad/bend.py` for the one piece of this that already has a real
implementation and unit tests.

Open naming question this file takes a position on (flag if wrong): `direction` on a
*nested* bend is "up" if the fold continues rotating the same way as its parent already
did (away from the part), "down" if it folds back the other way (toward the part) -- read
relative to the immediate parent flange, the same way you'd sequence bends on a real
press brake, one joint at a time. For this tray that gives the same answer either way
Martin's "relative to the unfolded, still-flat part" phrasing could be taken, so it
doesn't matter here -- but it's worth confirming before the two readings diverge on a
trickier part.
"""

SPEC = """
# Sheet-Metal Aluminium Tray - Engineering Specification

## 1. Material

Manufacture the component from:

* **Material:** Aluminium alloy **5052-H32**
* **Nominal sheet thickness:** **2.0 mm**
* **Material condition:** H32 (half-hard)
* **Units:** All dimensions are in millimetres (mm).

5052-H32 is specified as a suitable general-purpose sheet-metal aluminium alloy with good corrosion resistance and good formability.

## 2. Base

The finished base is nominally:

* **Length:** 440 mm
* **Width:** 89 mm

The base is formed from a single sheet-metal blank and is bent upward on all four sides.

## 3. Long-side flanges

Both long sides of the base are bent upward to form vertical flanges.

* **Flange height:** 200 mm
* **Bend angle:** 90 deg
* **Inside bend radius:** 2 mm
* **K-factor:** 0.42

The long-side flanges are to remain vertical.

### Front long-side flange

The front long-side flange incorporates an additional inward-facing return flange:

* **Return flange:** 10 mm
* **Return bend:** 90 deg inward
* **Inside bend radius:** 2 mm
* **K-factor:** 0.42

The 10 mm dimension refers to the length of the finished return flange.

## 4. Short-side flanges

Both short sides are bent upward to form vertical flanges.

* **Flange height:** 200 mm
* **Bend angle:** 90 deg
* **Inside bend radius:** 2 mm
* **K-factor:** 0.42

At the top of each short-side flange, the flange is bent outward by 90 deg.

* **Outward flange length:** 30 mm
* **Bend angle:** 90 deg
* **Inside bend radius:** 2 mm
* **K-factor:** 0.42

The two outward-facing 30 mm flanges have their outer corners rounded:

* **Corner radius:** R6 mm

The R6 radius applies to the plan-view corners of the outward-facing flanges and is not the sheet-metal bend radius.

## 5. Bend and fabrication assumptions

For the purposes of this reference design, use the following bend parameters for all 90 deg sheet-metal bends:

| Parameter                              |      Specification |
| --------------------------------------- | ------------------: |
| Material                               | Aluminium 5052-H32 |
| Sheet thickness                        |             2.0 mm |
| Inside bend radius                     |             2.0 mm |
| Bend angle                             |                90 deg |
| K-factor                               |               0.42 |
| Outside corner radius on short flanges |              R6 mm |

The K-factor of **0.42** is to be used for calculating bend allowance and the flat-pattern dimensions.

Actual bend allowance should be verified against the sheet-metal brake, tooling, material batch, and forming method used for production. The dimensions above describe the **finished component**, not the dimensions of the initial flat blank.

## 6. General fabrication requirements

The component should be manufactured as a single-piece sheet-metal component wherever practical.

All bends should be clean 90 deg bends with consistent bend radii. Finished dimensions should be measured after forming.

The 440 x 89 mm base dimension and the 200 mm flange heights are finished dimensions. The fabricator should calculate the flat-pattern dimensions using the specified material thickness, inside bend radius, and K-factor rather than simply adding the nominal flange dimensions together.

Deburr all cut edges and remove sharp edges after fabrication.

The R6 corner radii on the outward-facing short-side flanges should be cut/form-processed before or during fabrication as appropriate for the chosen manufacturing process.
"""
from pathlib import Path

from cycax.cycad import SheetMetalBend
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.engines.part_freecad_bend import PartEngineFreeCADBend

tray = SheetMetalBend(
    part_no="aluminium_tray",
    x_size=440.0,  # length -> front/back are the "long" 440 mm sides
    y_size=89.0,  # width  -> left/right are the "short" 89 mm sides
    z_size=2.0,  # sheet thickness
    material={"name": "aluminium", "code": "5052-H32", "standard": "AISI"},
    k_factor=0.42,
    bend_radius=2.0,  # inside bend radius; every bend below uses this part-level default
)

# --- Long sides (440 mm): plain 200 mm vertical walls, except front gets a return lip. ---

back_wall = tray.back.bend(angle=90, height=200.0, direction="up")

front_wall = tray.front.bend(angle=90, height=200.0, direction="up")
front_lip = front_wall.far.bend(angle=90, height=10.0, direction="up")
# .far == "the edge opposite the fold that created this flange" -- the common case for
# continuing a chain. front_wall also still exposes .left/.right/.front/.back directly
# (any edge, not just .far) for the rarer case of bending off one of a flange's side
# edges instead -- not needed here, but part of the decided design (bending-design.md
# open question #1: "any edge", not just the far one).

# --- Short sides (89 mm): 200 mm vertical walls, each with an outward-folded tip. ---

left_wall = tray.left.bend(angle=90, height=200.0, direction="up")
left_tip = left_wall.far.bend(angle=90, height=30.0, direction="down")  # continues outward

right_wall = tray.right.bend(angle=90, height=200.0, direction="up")
right_tip = right_wall.far.bend(angle=90, height=30.0, direction="down")

# The two outward tips get their outer plan-view corners rounded. Deliberately NOT
# CycadPart.beveled_edge() -- Martin wants sheet-metal corner rounding kept as its own,
# dedicated mechanism rather than reusing the generic edge-bevel primitive, even though
# the two happen to cut similar-looking geometry. round_corners() below is that dedicated
# call; it also marks left_tip/right_tip as terminal -- calling .bend() on either again
# after this point should raise.
left_tip.round_corners(radius=6.0)
right_tip.round_corners(radius=6.0)

tmp_path = Path("/tmp/bend/b123")
tray.save(path=tmp_path)
engine = PartEngineBuild123d(name=tray.part_no, path=tmp_path)
tray.build(engine)

tmp_path = Path("/tmp/bend/fc")
tray.save(path=tmp_path)
engine = PartEngineFreeCADBend(name=tray.part_no, path=tmp_path)
tray.build(engine)
# --- Same tray, `with`-block style for the nested pair (both styles are meant to work) ---
#
# with tray.left.bend(angle=90, height=200.0, direction="up") as left_wall:
#     with left_wall.far.bend(angle=90, height=30.0, direction="up") as left_tip:
#         left_tip.round_corners(radius=6.0)
