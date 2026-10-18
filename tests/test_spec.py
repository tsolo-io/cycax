# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# Spec version 2: validation, the meta/hash rule, and the published JSON Schemas.
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from cycax.cycad import Assembly, SheetMetal, SheetMetalBend
from cycax.spec import SpecVersionError, json_schemas, spec_hash, validate_spec
from cycax.targets import load_targets


def _plate(**kwargs):
    return SheetMetal(part_no="plate", x_size=60, y_size=40, z_size=2, **kwargs)


def test_part_export_is_valid_v2():
    spec = _plate().export()
    assert spec["spec_version"] == 2  # noqa: PLR2004
    assert spec["kind"] == "part"
    validate_spec(spec)


def test_meta_does_not_change_the_hash():
    plain = _plate()
    described = _plate()
    described.description = "A plate."
    described.notes = "Long *Markdown* notes."
    described.colour = "red"
    assert plain.export()["meta"] != described.export()["meta"]
    assert spec_hash(plain.export()) == spec_hash(described.export())


def test_material_is_meta_but_geometry_is_hashed():
    steel = SheetMetalBend(part_no="b", x_size=80, y_size=50, z_size=3)
    alu = SheetMetalBend(part_no="b", x_size=80, y_size=50, z_size=3, material={"name": "aluminium", "code": "5052"})
    assert spec_hash(steel.export()) == spec_hash(alu.export())
    longer = SheetMetalBend(part_no="b", x_size=90, y_size=50, z_size=3)
    assert spec_hash(steel.export()) != spec_hash(longer.export())


def test_assembly_colour_does_not_change_the_hash():
    def build(colour):
        assembly = Assembly("a")
        part = _plate()
        part.colour = colour
        assembly.add(part)
        return assembly.export()

    assert spec_hash(build("red")) == spec_hash(build("blue"))


def test_v1_spec_is_rejected_with_a_clear_message():
    with pytest.raises(SpecVersionError, match="expected 2"):
        validate_spec({"name": "old", "features": []})


def test_invalid_v2_spec_is_rejected():
    spec = _plate().export()
    spec["features"] = []
    with pytest.raises(ValidationError):
        validate_spec(spec)


def test_published_schemas_are_current():
    folder = Path(__file__).parents[1] / "src" / "cycax" / "spec" / "schemas"
    for filename, schema in json_schemas().items():
        assert json.loads((folder / filename).read_text()) == schema, f"Run `python -m cycax.spec` ({filename})"


def test_docstring_and_doc_view_go_to_meta(tmp_path):
    src = tmp_path / "parts.py"
    src.write_text(
        "from cycax import SheetMetal, cycax_part\n\n"
        "@cycax_part(doc_view='top')\n"
        "def plate():\n"
        "    '''A plate with a hole.'''\n"
        "    part = SheetMetal(part_no='plate', x_size=60, y_size=40, z_size=2)\n"
        "    part.top.hole(pos=(30, 20), diameter=5)\n"
        "    return part\n"
    )
    (target,) = load_targets(src)
    (part,) = target.make()
    meta = part.export()["meta"]
    assert meta["description"] == "A plate with a hole."
    assert meta["doc_view"] == "top"


def test_hash_vector_shared_with_cycax_server():
    # The same vector is checked in cycax-server (tests/test_spec.py), which has its own copy.
    vector = {
        "spec_version": 2,
        "kind": "part",
        "name": "vector",
        "features": [
            {
                "type": "cuboid",
                "action": "add",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "x_size": 10.0,
                "y_size": 20.0,
                "z_size": 2.0,
            }
        ],
        "subtract": [],
        "meta": {"colour": [1.0, 0.0, 0.0], "notes": "ignored"},
    }
    assert spec_hash(vector) == "8ba1034e7264acd2"
