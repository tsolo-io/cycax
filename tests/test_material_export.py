# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import SheetMetal, SheetMetalBend


def test_sheet_metal_bend_exports_its_material():
    material = {"name": "aluminium", "code": "5052-H32", "standard": "AISI"}
    part = SheetMetalBend(part_no="bracket", x_size=80, y_size=50, z_size=3, material=material)
    # A standard material: the density comes from cycax.materials (cycax/24).
    assert part.export()["meta"]["material"] == material | {"density": 2.68}


def test_default_material_is_exported():
    part = SheetMetalBend(part_no="bracket", x_size=80, y_size=50, z_size=3)
    assert part.export()["meta"]["material"]["name"] == "mild-steel"


def test_part_without_material_has_no_material_key():
    assert "material" not in SheetMetal(part_no="plate", x_size=10, y_size=10, z_size=2).export()["meta"]


def test_assembly_entries_carry_the_material_for_renderers():
    from cycax.cycad import Assembly  # noqa: PLC0415

    assembly = Assembly("pair")
    assembly.add(SheetMetalBend(part_no="bracket", x_size=80, y_size=50, z_size=3))
    assembly.add(SheetMetal(part_no="plate", x_size=10, y_size=10, z_size=2))
    entries = {entry["name"]: entry for entry in assembly.export()["parts"]}
    assert entries["bracket"]["meta"]["material"]["name"] == "mild-steel"
    assert "material" not in entries["plate"]["meta"]
