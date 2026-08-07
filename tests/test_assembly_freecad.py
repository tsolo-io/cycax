# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import tempfile
from pathlib import Path

import pytest

from cycax.cycad import Assembly, AssemblyFreeCAD, SheetMetal


def test_freecad_assembly_creation():
    """Test that FreeCAD assembly engine can be created."""
    assembly_engine = AssemblyFreeCAD("test_assembly")
    assert assembly_engine.name == "test_assembly"
    assert assembly_engine._parts == []


def test_freecad_assembly_add_parts():
    """Test that parts can be added to FreeCAD assembly engine."""
    assembly_engine = AssemblyFreeCAD("test_assembly")

    part_operation = {
        "name": "test_part",
        "x": 0,
        "y": 0,
        "z": 0,
        "rotate": [],
        "x_size": 10,
        "y_size": 10,
        "z_size": 10,
        "colour": [1.0, 0.5, 0.0],
        "hash": "test_hash",
    }

    assembly_engine.add(part_operation)
    assert len(assembly_engine._parts) == 1
    assert assembly_engine._parts[0]["name"] == "test_part"


def test_assembly_get_freecad_assembler():
    """Test that Assembly class can create FreeCAD assembler."""
    assembly = Assembly("test_assembly")

    # Test that FreeCAD engine can be retrieved
    assembler = assembly._get_assembler(engine="FreeCAD")
    assert isinstance(assembler, AssemblyFreeCAD)
    assert assembler.name == "test_assembly"


def test_assembly_export_for_freecad():
    """Test that assembly can export data for FreeCAD engine."""
    assembly = Assembly("box_assembly")
    part1 = SheetMetal(x_size=100, y_size=50, z_size=2, part_no="bottom")
    part2 = SheetMetal(x_size=100, y_size=20, z_size=2, part_no="front")

    assembly.add(part1, "bottom")
    assembly.add(part2, "front")

    # Export assembly data
    data = assembly.export()

    assert data["name"] == "box_assembly"
    assert len(data["parts"]) == 2
    assert data["parts"][0]["name"] == "bottom"
    assert data["parts"][1]["name"] == "front"


@pytest.mark.ci_exclude
def test_freecad_assembly_build_without_freecad():
    """Test FreeCAD assembly build behavior when FreeCAD is not available."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        assembly_engine = AssemblyFreeCAD("test_assembly", config={})
        assembly_engine._base_path = tmppath

        part_operation = {
            "name": "test_part",
            "x": 0,
            "y": 0,
            "z": 0,
            "rotate": [],
            "x_size": 10,
            "y_size": 10,
            "z_size": 10,
            "colour": [1.0, 0.5, 0.0],
            "hash": "test_hash",
        }

        assembly_engine.add(part_operation)

        # This should handle gracefully when FreeCAD is not found
        # The build method logs errors but doesn't raise exceptions
        assembly_engine.build(tmppath)

        # Check that assembly JSON was created
        json_file = tmppath / "test_assembly.json"
        assert json_file.exists()
