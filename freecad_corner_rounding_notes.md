# FreeCAD corner-rounding / flange-cutout positioning: resolved

Status: **Fixed.** Kept for the record of what was wrong and how it was found, since the same
class of bug (idealised vs. real geometry mismatch) is likely to resurface in some new shape.

## What was wrong

Two related but distinct bugs, both in `src/cycax/cycad/engines/cycax_part_freecad_bend.py`:

1. **Corner rounding was asymmetric between the two tips of the tray** (`bend.py`): the left
   tip's `flange_corner_round` cut correctly removed material; the right tip's cut tool was
   correctly sized and shaped but sat entirely under the real flange, removing nothing.
   Confirmed by volume, not just visual inspection: `Cut_1`'s volume dropped by exactly the
   corner-round tool's own volume; `Cut_2`'s didn't move at all. Root cause: `z_start`
   (which side of the cut's own local plane the material extends into) was picked from
   `points_outward` alone, which isn't reliably predictable for a *nested* bend (the tip is a
   bend off a wall, itself a bend).

   Martin's own diagnosis nailed it exactly: *"The cutout is under the flange. Move the
   cutout up (increase Z) and it will cut."* Fix: build both `z_start` candidates and keep
   whichever one actually overlaps the real solid (`shape.common(solid).Volume`), rather than
   trusting the sign convention -- same fix applied to `_extruded_flat_cut` (rectangle/polygon
   cuts) and `_flange_hole_tool` (holes on a flange).

2. **Cutout *position* on a flange (hole/rectangle/polygon centre) didn't match the real,
   rounded-bend-radius geometry.** A first attempt corrected this by shifting the idealised
   centre by `-n_dir * radius` -- verified against two "up"-direction bends (matched exactly
   both times) but then failed completely on `bend2.py`'s `front_flange`/`back_flange`
   ("down"-direction, gap-narrowed flanges): the real material there wasn't where that formula
   predicted at all, in any direction. Root cause: the curved bend region's real footprint is
   anchored to the *parent* surface's own normal at the fold, not necessarily this flange's own
   (rotated) `n_dir` -- so a fixed "offset by this bend's radius, along this bend's own n_dir"
   rule doesn't generalise across bend directions.

   Fixed properly this time by not guessing a formula at all: `_flange_face_offset` searches
   the real solid directly for the planar face whose normal matches `n_dir` (outward, not
   antiparallel) and whose footprint plausibly contains the idealised centre, and uses
   whichever such face is closest. This is the same "search real geometry, don't trust
   idealised coordinates" pattern already used for `_find_edge` (bend fold-lines) -- turns out
   it was needed here too, and a hand-derived offset formula wasn't a reliable substitute for
   it.

## How it was verified

Not by eyeballing -- by comparing volumes precisely:

- Built `bend.py`'s tray and `bend2.py`'s bracket through the real `FreeCADBend` engine.
- Read each `Part::Cut` object's own `.Shape.Volume` and diffed against its `.Base`'s volume,
  per cut, to get the *exact* amount of material each cut removed.
- Compared against hand-computed expected volumes (hole = `pi*r^2*thickness`, rectangle =
  `w*h*thickness`, hexagon = `(3*sqrt(3)/2*r^2)*thickness`, rounded rectangle =
  `(w*h - (4-pi)*r^2)*thickness`, corner-round pair = `2*(r^2 - pi*r^2/4)*thickness`) -- matched
  to within float precision in every case, on both the tray (corner-rounds) and the bracket
  (corner-rounds + M12 clearance holes on gap-narrowed, "down"-direction flanges).

## Takeaway for next time

Whenever a cut/cutout's shape looks right in isolation but doesn't visibly do anything (or does
something asymmetric between otherwise-similar features), check for exactly this pattern first:
volume-diff each `Part::Cut` in the chain against its own `.Base`, rather than trying to eyeball
correctness or guess at a coordinate formula. It's cheap, exact, and was what actually found both
bugs here -- `isInside()` point-sampling at guessed coordinates missed the second bug entirely
(the guessed probe points were themselves based on the same wrong formula).
