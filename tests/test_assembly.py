# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad import Assembly, SheetMetal


def test_part_names():
    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="test_part")
    mypart2 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="test_part")
    assembly.add(mypart1)
    assembly.add(mypart2)
    assert list(assembly.parts.keys()) == ["test_part_1", "test_part_2"], "The parts names are correct."
    assert mypart1 is assembly.get_part("test_part_1"), "The same part is return when accessed through get_part."
    assert mypart2 is assembly.get_part("test_part_2"), "The same part is return when accessed through get_part."
    parts = assembly.get_parts_by_no("test_part")
    assert mypart1 in parts, "Part1 is in parts list."
    assert mypart2 in parts, "Part2 is in parts list."
    mypart3 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="test_part")
    assembly.add(mypart3, "top")
    assert list(assembly.parts.keys()) == ["test_part_1", "test_part_2", "top"], "The parts names are correct."
    assert mypart3 is assembly.get_part("top"), "The same part is return when accessed through get_part."


def test_export_part_entry_shape():
    """The exported per-part dict follows the new data-file-spec-new.md field names."""
    assembly = Assembly("shape-test")
    part = SheetMetal(x_size=10, y_size=20, z_size=2, part_no="a_part")
    assembly.add(part)

    data = assembly.export()

    assert data == {
        "name": "shape_test",
        "parts": [
            {
                "name": "a_part",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "x_size": 10,
                "y_size": 20,
                "z_size": 2,
                "rotate": [],
                "colour": [0.5, 0.5, 0.5],
                "hash": "",
            }
        ],
    }


def test_nested_assembly_is_flattened_automatically():
    """A nested Assembly added via .add() is flattened into the parent's exported parts
    without the caller having to call combine_all_assemblies() first."""
    outer = Assembly("outer")
    inner = Assembly("inner")
    outer_part = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="outer_part")
    inner_part = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="inner_part")

    outer.add(outer_part)
    inner.add(inner_part)
    outer.add(inner)

    data = outer.export()

    # The exported "name" is each part's own part_no (needed so engines can still find the
    # part's built files on disk); only the *internal* dict key used to merge parts from
    # different nested assemblies gets a disambiguating prefix.
    names = {p["name"] for p in data["parts"]}
    assert names == {"outer_part", "inner_part"}
    assert all("parts" not in p for p in data["parts"]), "Nested assemblies are never stored as such."
