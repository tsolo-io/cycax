# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Materials (task cycax/24)."""

import pytest

from cycax.cycad import Print3D, SheetMetal
from cycax.cycad.sheetmetal_bend import SheetMetalBend
from cycax.materials import ALUMINIUM_5052_H32, MILD_STEEL_1008, PLA, Material, as_material, by_key
from cycax.spec import spec_hash


def test_standard_set():
    assert by_key("aluminium", "5052-H32") is ALUMINIUM_5052_H32
    assert by_key("pla") is PLA
    assert ALUMINIUM_5052_H32.mass_g(1000.0) == pytest.approx(2.68)


def test_material_goes_into_meta_not_the_hash():
    plain = Print3D(part_no="cover", x_size=10, y_size=10, z_size=2)
    pla = Print3D(part_no="cover", x_size=10, y_size=10, z_size=2, material=PLA)
    assert pla.export()["meta"]["material"] == {"name": "PLA", "density": 1.24}
    assert spec_hash(plain.export()) == spec_hash(pla.export())


def test_colour_comes_from_the_material_when_not_set():
    assert Print3D(part_no="a", x_size=1, y_size=1, z_size=1, material=PLA).export()["meta"]["colour"] == list(
        PLA.colour
    )
    assert Print3D(part_no="a", x_size=1, y_size=1, z_size=1).export()["meta"]["colour"] == [1.0, 0.0, 0.0]
    part = SheetMetal(part_no="a", x_size=1, y_size=1, material=ALUMINIUM_5052_H32, colour="blue")
    assert part.export()["meta"]["colour"] == [0.0, 0.0, 1.0]
    part.colour = "green"
    assert part.export()["meta"]["colour"] == [0.0, 1.0, 0.0]


def test_project_material():
    acrylic = Material("acrylic", grade="cast", density=1.19, colour=(0.9, 0.95, 1.0))
    part = SheetMetal(part_no="cover", x_size=100, y_size=60, z_size=3, material=acrylic)
    meta = part.export()["meta"]
    assert meta["material"] == {"name": "acrylic", "code": "cast", "density": 1.19}
    assert meta["colour"] == [0.9, 0.95, 1.0]


def test_old_material_dict_still_works():
    assert as_material({"name": "aluminium", "code": "5052-H32"}) is ALUMINIUM_5052_H32
    assert as_material({"name": "aluminium", "code": "5052-H32", "standard": "AISI"}).density == 2.68
    custom = as_material({"name": "brass", "code": "C360"})
    assert custom.name == "brass"
    assert custom.density == 0.0
    with pytest.raises(TypeError):
        as_material("PLA")


def test_sheet_metal_defaults_from_the_material():
    default = SheetMetalBend(part_no="b", x_size=50, y_size=20, z_size=2)
    assert default.material is MILD_STEEL_1008
    assert default.k_factor == pytest.approx(0.44)
    assert default.bend_radius == pytest.approx(2.0)
    aluminium = SheetMetalBend(part_no="b", x_size=50, y_size=20, z_size=2, material=ALUMINIUM_5052_H32)
    assert aluminium.k_factor == pytest.approx(0.43)
    own = SheetMetalBend(part_no="b", x_size=50, y_size=20, z_size=2, material=ALUMINIUM_5052_H32, k_factor=0.4)
    assert own.k_factor == pytest.approx(0.4)


def test_local_summary_has_the_mass(tmp_path):
    import json

    import cycax

    part = SheetMetal(part_no="alu_plate", x_size=100, y_size=50, z_size=2, material=ALUMINIUM_5052_H32)
    result = cycax.build(part, outputs=["summary"], backend="local", project_dir=tmp_path)
    summary = json.loads(result.files["summary"].read_text())
    assert summary["mass_g"] == pytest.approx(26.8)
    assert summary["bbox_mm"]["size"] == [100.0, 50.0, 2.0]
