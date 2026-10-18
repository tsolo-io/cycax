<!--
SPDX-FileCopyrightText: 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Materials

A part can have a material. The material gives:

- the mass in reports and in `summary.json` (density),
- the colour of the part, when the part has no colour of its own,
- for sheet-metal parts, the default K-factor and bend radius.

The material is in the spec `meta`, so a change of material does not change the hash and does
not cause a new build. The K-factor and the bend radius are geometry, so they are in the hash.

## Standard materials

| Python name | Material | Grade | Density g/cm³ | K-factor | Bend radius |
|---|---|---|---|---|---|
| `STAINLESS_STEEL_304` | stainless-steel | 304 | 8.00 | 0.45 | 1 × thickness |
| `ALUMINIUM_5052_H32` | aluminium | 5052-H32 | 2.68 | 0.43 | 1 × thickness |
| `MILD_STEEL_1008` | mild-steel | 1008 | 7.87 | 0.44 | 1 × thickness |
| `PLA` | PLA | | 1.24 | | |
| `PETG` | PETG | | 1.27 | | |

These are typical values. Check them against the data of your supplier.

```python
from cycax.cycad import Print3D, SheetMetalBend
from cycax.materials import ALUMINIUM_5052_H32, PETG

bracket = SheetMetalBend(part_no="bracket", x_size=80, y_size=50, z_size=2, material=ALUMINIUM_5052_H32)
clip = Print3D(part_no="clip", x_size=20, y_size=10, z_size=5, material=PETG)
```

`SheetMetalBend` uses mild steel 1008 when you give no material. `k_factor=` and
`bend_radius=` on the part override the defaults of the material.

## Project materials

Define the materials of a project in a Python module and import them like parts:

```python
# materials.py in your project
from cycax.materials import Material

ACRYLIC_CLEAR = Material("acrylic", grade="cast", density=1.19, colour=(0.9, 0.95, 1.0))
ALUMINIUM_6061 = Material(
    "aluminium", grade="6061-T6", standard="AA", density=2.70, colour=(0.85, 0.86, 0.88),
    k_factor=0.42, bend_radius_factor=1.5,
)
```

In the spec, `meta.material` is `{"name", "code", "standard", "density"}` (`code` is the grade).

# Manufacturing

A part can say how it is made: the process, the machine, the settings, the quantity and the
instructions for a person. It is in the spec `meta.manufacture` (not hashed). Reports show the
process and the instructions. Machine outputs (slicer files, CNC tool paths) come later.

| Python object | Process | Default for |
|---|---|---|
| `FdmPrint(printer=, filament=, layer=0.2, infill=20, supports=False)` | `3d-print` | `Print3D` |
| `LaserCut(machine=)` | `laser-cut` | `SheetMetal` |
| `LaserCutAndBend(machine_cut=, machine_bend=)` | `laser-cut-and-bend` (two steps) | `SheetMetalBend` |
| `CncMill(machine=, stock=, tools=[...])` | `cnc-mill` | — |
| `Manufacture(process=, machine=, settings=, quantity=, instructions=)` | any | — |

```python
from cycax.manufacture import FdmPrint
from cycax.materials import PLA

clip = Print3D(part_no="clip", x_size=20, y_size=10, z_size=5, material=PLA,
               manufacture=FdmPrint(printer="Prusa MK4", filament="red PLA", infill=30))
# instructions: "3D print with red PLA filament on the Prusa MK4, layer 0.2 mm, infill 30 %, no supports."
```

Without `instructions=`, CyCAx makes the sentence from the other fields and the material.
