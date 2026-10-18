<!--
SPDX-FileCopyrightText: 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Sketches and DXF

A `Sketch` is a set of closed 2D profiles in mm. A profile inside another profile is a hole.

| Method | Profile |
|---|---|
| `rectangle(x, y, width, height, radius=0)` | lower-left corner at (x, y); `radius` rounds the corners |
| `circle(x, y, diameter=)` | |
| `polygon(x, y, sides=, diameter=, angle=0)` | a regular polygon; `diameter` through the corners |
| `slot(x, y, length=, width=, angle=0)` | from the centre of one round end, `length` to the other |
| `polyline(points)` | a closed polygon |
| `Sketch.from_dxf(file, scale=None, layer=None)` | closed outlines of a DXF file |

```python
from cycax import cycax_part
from cycax.cycad import Sketch, SketchPart


@cycax_part
def plate() -> SketchPart:
    """An 80 x 40 mm plate with rounded corners, two holes and a pocket."""
    outline = Sketch().rectangle(0, 0, 80, 40, radius=5)
    for x in (10, 70):
        outline.circle(x, 20, diameter=4.2)
    part = SketchPart(part_no="plate", sketch=outline, thickness=3)  # pad 3 mm up
    part.top.pocket(Sketch().rectangle(30, 10, 20, 20), depth=1)      # 1 mm deep pocket
    part.front.boss(Sketch().circle(40, 1.5, diameter=2), height=5)   # a pin on the front
    return part
```

- `SketchPart(part_no, sketch, thickness)` pads the sketch up from the XY plane.
  `SketchPart(..., revolve={"axis": [[0, 0], [0, 1]], "angle": 360})` revolves it about the axis
  through two sketch points.
- `part.<side>.pocket(sketch, depth=None)` cuts into a side (no depth: through);
  `part.<side>.boss(sketch, height)` adds onto a side. The sketch points use the same
  coordinates as `pos` of `hole()` on that side.

## DXF

`Sketch.from_dxf("bracket.dxf")` reads LWPOLYLINE/POLYLINE (with arcs), CIRCLE, and closed
chains of LINE and ARC. The units come from the file (`$INSUNITS`: mm, cm, m, inch, foot, ...).
When the file has no units, give the scale (mm per drawing unit): `scale=1.0` for mm, `25.4` for
inches; without it CyCAx stops with an error. `layer=` reads one layer only.

The DXF is converted when the part is made: the spec holds the profiles, the file name and the
file's SHA-256, so a changed file gives a new hash and the workers do not need the file.

SVG import is not there yet.

Engines: build123d now; the FreeCAD worker (task freecad/09) next.
