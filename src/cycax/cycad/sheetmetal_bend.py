# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""`SheetMetalBend`: a standalone part type for laser-cut, bent sheet-metal parts.

See docs/content/sheetmetal-bend-design.md for the full design. Deliberately does not
subclass `SheetMetal` (`cuboid.py`) -- that class is shared with `Print3D` today and is
left alone; bending has its own part type and its own dedicated `FreeCADBend` engine
instead of being bolted onto the existing one.
"""

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid


class SheetMetalBend(Cuboid):
    """A flat rectangular sheet that can be bent into flanges and cut with 2D shapes.

    Always starts as a flat sheet on the XY plane at (0, 0, 0): `z_size` (the sheet
    thickness) is expected to be smaller than `x_size`/`y_size`, which may be equal to
    each other. Bends are added via `.bend()` on `left`/`right`/`front`/`back`
    (`CycadSide.bend()`, delegating to `cycax.cycad.bend.root_bend_side`); cutouts
    (`hole`/`rectangle`/`rounded_rectangle`/`polygon`) are available both on the base
    sheet's faces and on any flange returned by a bend.

    Args:
        x_size: The size of x.
        y_size: The size of y.
        z_size: The size of z. Also used as the sheet thickness.
        part_no: The unique name that will be given to a type of parts.
        assembly: The assembly the part belongs to.
        material: The material (`cycax.materials.Material`; an old `{"name", "code",
            "standard"}` dict also works). Default: mild steel 1008. It goes into the spec meta
            (not hashed) and gives the defaults of `k_factor` and `bend_radius`.
        k_factor: Default bend-allowance K-factor used by `bend()` when a bend doesn't
            specify its own. Default: the K-factor of the material (mild steel: 0.44).
        bend_radius: Default inside bend radius used by `bend()` when a bend doesn't
            specify its own, and by every bend in the part (`sheetmetal-bend-design.md`
            deliberately doesn't support a per-bend radius override). Defaults to the
            sheet thickness (`z_size`) times the material's `bend_radius_factor` (1.0).
    """

    def __init__(
        self,
        part_no: str,
        x_size: float,
        y_size: float,
        z_size: float = 2.0,
        assembly: Assembly | None = None,
        material=None,
        k_factor: float | None = None,
        bend_radius: float | None = None,
        colour: str | None = None,
        manufacture=None,
    ):
        from cycax.materials import MILD_STEEL_1008, as_material  # noqa: PLC0415

        material = as_material(material) or MILD_STEEL_1008
        super().__init__(
            part_no=part_no,
            x_size=x_size,
            y_size=y_size,
            z_size=z_size,
            assembly=assembly,
            material=material,
            colour=colour,
            manufacture=manufacture,
        )
        # Geometry (hashed): from the arguments, else the defaults of the material.
        self.k_factor = k_factor if k_factor is not None else (material.k_factor or 0.44)
        if bend_radius is None:
            bend_radius = z_size * (material.bend_radius_factor or 1.0)
        self.bend_radius = bend_radius

    def default_manufacture(self):
        from cycax.manufacture import LaserCutAndBend  # noqa: PLC0415

        return LaserCutAndBend()
