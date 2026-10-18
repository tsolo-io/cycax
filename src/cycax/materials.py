# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Materials (task cycax/24).

A material is a Python object, so a project defines its own materials in a module and imports
them like parts:

    # myproject/materials.py
    from cycax.materials import Material
    ACRYLIC_CLEAR = Material("acrylic", grade="cast", density=1.19, colour=(0.9, 0.95, 1.0))

    # myproject/parts/cover.py
    from myproject.materials import ACRYLIC_CLEAR
    cover = SheetMetal(part_no="cover", x_size=100, y_size=60, z_size=3, material=ACRYLIC_CLEAR)

The material goes into the spec `meta` (it does not change the hash). The K-factor and the
bend radius of a sheet-metal part are geometry, so they are hashed; the material only gives
their defaults.

The values of the standard set are typical values. Check them against the data of your
supplier before you use a mass for a quotation.
"""

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Material:
    """A material.

    Attributes:
        name: The material name, e.g. "aluminium".
        grade: The grade or alloy code, e.g. "5052-H32".
        density: g/cm³.
        colour: RGB, each 0.0 to 1.0. A part without its own colour gets this colour.
        standard: The standard of the grade, e.g. "AISI", "EN".
        k_factor: Sheet metal: the default K-factor for bends.
        bend_radius_factor: Sheet metal: the default inside bend radius as a factor of the
            sheet thickness.
        notes: Free text (supplier, finish, ...).
    """

    name: str
    grade: str = ""
    density: float = 0.0
    colour: tuple[float, float, float] = (0.6, 0.6, 0.6)
    standard: str = ""
    k_factor: float | None = None
    bend_radius_factor: float | None = None
    notes: str = field(default="", compare=False)

    @property
    def key(self) -> str:
        """A short unique name, e.g. "aluminium-5052-h32"."""
        return "-".join(part for part in (self.name, self.grade) if part).lower().replace(" ", "-")

    def to_meta(self) -> dict:
        """The spec `meta.material` object (docs/content/data-file-spec.md)."""
        meta = {"name": self.name}
        if self.grade:
            meta["code"] = self.grade
        if self.standard:
            meta["standard"] = self.standard
        if self.density:
            meta["density"] = self.density
        return meta

    def mass_g(self, volume_mm3: float) -> float:
        """The mass in grams of `volume_mm3` of this material."""
        return volume_mm3 / 1000.0 * self.density

    @classmethod
    def from_meta(cls, data: dict) -> "Material":
        """A material from a spec `meta.material` object (or the old `{name, code, standard}` dict)."""
        known = by_key(data.get("name", ""), data.get("code", ""))
        if known is not None:
            # A standard material: its density, colour and sheet-metal defaults; the
            # standard of the grade as given.
            standard = data.get("standard")
            return replace(known, standard=standard) if standard and standard != known.standard else known
        return cls(
            name=data.get("name", ""),
            grade=data.get("code", ""),
            standard=data.get("standard", ""),
            density=float(data.get("density", 0.0) or 0.0),
        )


STAINLESS_STEEL_304 = Material(
    "stainless-steel",
    grade="304",
    standard="AISI",
    density=8.00,
    colour=(0.78, 0.79, 0.80),
    k_factor=0.45,
    bend_radius_factor=1.0,
)
ALUMINIUM_5052_H32 = Material(
    "aluminium",
    grade="5052-H32",
    standard="AA",
    density=2.68,
    colour=(0.86, 0.87, 0.89),
    k_factor=0.43,
    bend_radius_factor=1.0,
)
MILD_STEEL_1008 = Material(
    "mild-steel",
    grade="1008",
    standard="AISI",
    density=7.87,
    colour=(0.45, 0.46, 0.48),
    k_factor=0.44,
    bend_radius_factor=1.0,
)
PLA = Material("PLA", density=1.24, colour=(0.95, 0.95, 0.93))
PETG = Material("PETG", density=1.27, colour=(0.85, 0.92, 0.95))

STANDARD_MATERIALS = (STAINLESS_STEEL_304, ALUMINIUM_5052_H32, MILD_STEEL_1008, PLA, PETG)


def by_key(name: str, grade: str = "") -> Material | None:
    """A standard material by name and grade (case does not matter)."""
    wanted = "-".join(part for part in (name, grade) if part).lower().replace(" ", "-")
    for material in STANDARD_MATERIALS:
        if material.key == wanted:
            return material
    return None


def as_material(value) -> Material | None:
    """A Material from a Material, a spec meta dict, or None."""
    if value is None or isinstance(value, Material):
        return value
    if isinstance(value, dict):
        return Material.from_meta(value)
    msg = f"Not a material: {value!r}. Use a cycax.materials.Material."
    raise TypeError(msg)
