# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Sheet-metal bending: second worked example, not yet backed by an implementation.

Status: DRAFT SYNTAX ONLY -- see bend.py's module docstring, same caveats apply. This
one exercises a different set of cases than bend.py: bends with a `gap1`/`gap2` relief
(a flange narrower than the edge it's bent from), a 3-stage curl where every bend keeps
the "up" default direction, holes on both the base and on a flange, and `round_corners()`
on a flange that's terminal after a single bend rather than a nested one.

Two things this file's reading of the spec assumes rather than states outright -- flag if
wrong:

1. "Long side flanges" (Section 3) are specified as 60 x 60 mm, but the base edge they're
   bent from is 80 mm long -- so the flange must be *narrower* than its edge, not a full-
   length flange like every one in bend.py. Modelled here with `gap1=gap2=10.0` (an equal
   10 mm relief at each end of the 80 mm edge -- see docs/content/bending-design.md's
   `bend()` signature draft, `gap1`/`gap2` already exist there for exactly this), which
   also centres the flange on the same edge the base is centred on.
2. Because of that centring, placing each flange's M12 hole at its own local centre
   (30, 30) satisfies "must lie on the same axis as the centre of the Ø30 mm hole" for
   free, without any extra alignment logic: both the base hole and the flange are centred
   on the same 80 mm edge, so their centrelines already coincide.

Also introduces a new bit of surface not yet in the design doc: `front_flange.hole(...)`
-- calling `.hole()` directly on the object `bend()` returns, drilling through the
flange's own thickness from its outward face, the same way `.top.hole()` already does on
a base part. Not decided anywhere yet, just used here because it's what reads naturally.
"""

SPEC = """
# Sheet-Metal Bracket / Grip - Engineering Specification

## 1. Material

Manufacture the component from:

* **Material:** Aluminium alloy **5052-H32**
* **Sheet thickness:** **3.0 mm**
* **Material condition:** H32 (half-hard)
* **Units:** All dimensions are in millimetres (mm).

5052-H32 is specified as a suitable sheet-metal aluminium alloy with good corrosion resistance and good formability.

## 2. Base

The component starts as a rectangular base:

* **Base width:** 50 mm
* **Base length:** 80 mm

A central hole is provided in the base:

* **Hole:** O30 mm
* **Hole position:** Centred on the 50 x 80 mm base.

The centre of the O30 mm hole defines the centreline for the bolt holes in the two side flanges.

## 3. Long-side flanges

The two long sides of the base are bent downward by 90 deg to form two opposing vertical flanges.

Each flange is:

* **Width:** 60 mm
* **Length/height:** 60 mm
* **Bend angle:** 90 deg downward
* **Inside bend radius:** 3 mm
* **K-factor:** 0.42

The lower corners of both flanges are rounded:

* **Corner radius:** R6 mm

The R6 radius applies to the external plan-view corners of the finished flange and is separate from the sheet-metal bend radius.

## 4. M12 bolt holes

Each of the two downward-facing side flanges has one hole suitable for an M12 bolt.

For a general-purpose M12 clearance hole, use:

* **Hole diameter:** O13 mm
* **Nominal bolt:** M12
* **Hole quantity:** 1 per side flange.

The bolt holes are positioned centrally in their respective 60 x 60 mm flanges.

The **centre of each M12 clearance hole must lie on the same axis as the centre of the O30 mm hole in the base**.

This alignment is important because the O30 mm opening is intended to accommodate a shaft, with the M12 bolt passing through the aligned side-flange holes to secure or retain the shaft.

The hole centres should therefore be treated as a common datum/centreline during manufacture rather than dimensioning each hole independently.

## 5. Short-side grip formation

The two short sides of the base are formed into an upward and inward grip profile.

The profile consists of three consecutive bends on each side.

### First bend

The short side of the base is bent upward by:

* **Bend angle:** 45 deg
* **Flange length:** 40 mm
* **Inside bend radius:** 3 mm
* **K-factor:** 0.42

### Second bend

The 40 mm flange is then bent through a further:

* **Bend angle:** 45 deg
* **Flange length:** 20 mm
* **Inside bend radius:** 3 mm
* **K-factor:** 0.42

This produces the second section of the grip profile.

### Third bend

The end of the 20 mm section is then bent through:

* **Bend angle:** 90 deg
* **Flange length:** 10 mm
* **Inside bend radius:** 3 mm
* **K-factor:** 0.42

The resulting 10 mm section forms the final inward-facing lip of the grip.

The complete profile is therefore:

**Base -> 45 deg / 40 mm -> 45 deg / 20 mm -> 90 deg / 10 mm**

The two short sides should be formed symmetrically so that the resulting grip geometry is identical on both sides.

## 6. Bend parameters

For this reference design, use the following parameters for flat-pattern and bend calculations:

| Parameter            |      Specification |
| --------------------- | ------------------: |
| Material             | Aluminium 5052-H32 |
| Sheet thickness      |             3.0 mm |
| Inside bend radius   |             3.0 mm |
| K-factor             |               0.42 |
| Standard bend angle  |                90 deg |
| Grip bend angles     |      45 deg, 45 deg, 90 deg |
| Flange corner radius |              R6 mm |

The **K-factor of 0.42** is to be used for calculating bend allowances and the flat-pattern dimensions.

The 3 mm inside bend radius is a nominal design value. Actual production tooling should be selected to achieve a suitable radius for 3 mm 5052-H32 aluminium.

## 7. Hole and feature alignment

The O30 mm base hole and the two M12 clearance holes are functionally related.

The following alignment requirement applies:

> The centreline of the O30 mm base hole shall be coincident with the centreline passing through the centres of the two M12 clearance holes.

The three holes therefore form a common axis through the finished component.

The position of the O30 mm hole should be established as the primary datum, with the two M12 hole positions referenced from this datum.

## 8. General fabrication requirements

The component should be manufactured from a single sheet-metal blank wherever practical.

All bends should be clean and consistent, with the specified bend angles maintained after forming.

The dimensions specified above are **finished-component dimensions**. The fabricator shall calculate the required flat-pattern dimensions using the material thickness, bend radius, bend angles, and K-factor.

Do not calculate the flat blank by simply adding the nominal flange dimensions, as this will not account for bend allowance.

All cut edges and holes shall be deburred.

The R6 mm corners on the downward side flanges shall be smooth and free from sharp edges.

The two grip profiles shall be symmetrical and aligned with each other.

The O30 mm base hole and both M12 clearance holes shall be checked for concentricity/alignment after forming.

### Reference geometry

The finished component comprises:

* 50 x 80 mm base.
* Central O30 mm shaft opening.
* Two 60 x 60 mm downward side flanges.
* One O13 mm M12 clearance hole in each side flange.
* M12 hole centres aligned with the O30 mm hole centre.
* R6 mm rounded corners on the downward side flanges.
* Two symmetrical grip profiles on the short sides.
* Each grip profile consists of:

  * 40 mm section at 45 deg.
  * 20 mm section after a further 45 deg bend.
  * 10 mm inward lip after a 90 deg bend.
* All sheet-metal bends use a nominal 3 mm inside radius and K-factor 0.42.
"""

from pathlib import Path

from cycax.cycad import SheetMetalBend
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.engines.part_freecad_bend import PartEngineFreeCADBend

bracket = SheetMetalBend(
    part_no="aluminium_bracket",
    x_size=80.0,  # length -> front/back are the "long" 80 mm sides
    y_size=50.0,  # width  -> left/right are the "short" 50 mm sides
    z_size=3.0,  # sheet thickness
    material={"name": "aluminium", "code": "5052-H32", "standard": "AISI"},
    k_factor=0.42,
    bend_radius=3.0,  # inside bend radius; every bend below uses this part-level default
)

# Central shaft hole, through the base, centred on the 80x50 footprint.
bracket.top.hole(pos=(40.0, 25.0), diameter=30.0)

# --- Long sides (80 mm): downward flanges, narrower than their own base edge. ---
# gap1=gap2=10.0 centres a 60 mm-wide flange on the 80 mm edge: (80 - 60) / 2 = 10 each end.

front_flange = bracket.front.bend(angle=90, height=60.0, direction="down", gap1=10.0, gap2=10.0)
front_flange.round_corners(radius=6.0)
front_flange.hole(pos=(30.0, 30.0), diameter=13.0)  # M12 clearance; centred, see module docstring

back_flange = bracket.back.bend(angle=90, height=60.0, direction="down", gap1=10.0, gap2=10.0)
back_flange.round_corners(radius=6.0)
back_flange.hole(pos=(30.0, 30.0), diameter=13.0)

# --- Short sides (50 mm): a 3-stage curl that keeps curling the same way throughout, so
# none of the three bends needs `direction` spelled out -- the "up" default carries the
# whole grip profile: base -> 45deg/40mm -> 45deg/20mm -> 90deg/10mm. ---

left_grip = bracket.left.bend(angle=45, height=40.0)
left_grip = left_grip.far.bend(angle=45, height=20.0)
left_grip = left_grip.far.bend(angle=90, height=10.0)

right_grip = bracket.right.bend(angle=45, height=40.0)
right_grip = right_grip.far.bend(angle=45, height=20.0)
right_grip = right_grip.far.bend(angle=90, height=10.0)

# bracket.save()

tmp_path = Path("/tmp/bend/b123")
bracket.save(path=tmp_path)
engine = PartEngineBuild123d(name=bracket.part_no, path=tmp_path)
bracket.build(engine)

tmp_path = Path("/tmp/bend/b123-brake")
bracket.save(path=tmp_path)
engine = PartEngineBuild123d(name=bracket.part_no, path=tmp_path, config={"bend_style": "brake_formed"})
bracket.build(engine)

tmp_path = Path("/tmp/bend/fc")
bracket.save(path=tmp_path)
engine = PartEngineFreeCADBend(name=bracket.part_no, path=tmp_path)
bracket.build(engine)
