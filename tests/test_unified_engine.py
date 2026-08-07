# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
import tempfile
from pathlib import Path

import pytest

from cycax.cycad.engines import Engine, EngineFreeCAD, EngineOpenSCAD


def test_engine_is_part():
    """Test that Engine can identify part JSON data."""
    engine = Engine()

    part_data = {"name": "test_part", "features": [{"type": "cuboid", "action": "add", "name": "cube"}]}
    assert engine.is_part(part_data)
    assert not engine.is_assembly(part_data)


def test_engine_is_assembly():
    """Test that Engine can identify assembly JSON data."""
    engine = Engine()

    assembly_data = {"name": "test_assembly", "parts": [{"part_no": "part1"}]}
    assert engine.is_assembly(assembly_data)
    assert not engine.is_part(assembly_data)


def test_engine_load_json():
    """Test that Engine can load JSON files."""
    engine = Engine()

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "test.json"
        test_data = {"name": "test", "features": []}
        json_file.write_text(json.dumps(test_data))

        loaded_data = engine.load_json(json_file)
        assert loaded_data == test_data


def test_engine_load_json_not_found():
    """Test that Engine raises error for missing JSON files."""
    engine = Engine()

    with pytest.raises(FileNotFoundError):
        engine.load_json(Path("/nonexistent/file.json"))


def test_engine_build_part_not_implemented():
    """Test that base Engine raises NotImplementedError for build_part."""
    engine = Engine()

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "test.json"
        json_file.write_text(json.dumps({"name": "test", "features": []}))

        with pytest.raises(NotImplementedError):
            engine.build_part(json_file)


def test_engine_build_assembly_not_implemented():
    """Test that base Engine raises NotImplementedError for build_assembly."""
    engine = Engine()

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "test.json"
        json_file.write_text(json.dumps({"name": "test", "parts": []}))

        with pytest.raises(NotImplementedError):
            engine.build_assembly(json_file)


def test_engine_file_list():
    """Test that Engine can generate file lists with metadata."""
    engine = Engine()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        test_file = tmppath / "test.stl"
        test_file.write_text("test")

        files = [{"file": test_file}]
        result = engine.file_list(files, "TestEngine", score=10)

        assert len(result) == 1
        assert result[0]["type"] == "STL"
        assert result[0]["engine"] == "TestEngine"
        assert result[0]["score"] == 10


def test_engine_file_list_nonexistent():
    """Test that Engine handles nonexistent files in file_list."""
    engine = Engine()

    files = [{"file": Path("/nonexistent/file.stl")}]
    result = engine.file_list(files, "TestEngine")

    assert len(result) == 0


def test_freecad_engine_creation():
    """Test that FreeCAD engine can be created."""
    engine = EngineFreeCAD()
    assert engine.engine_name == "FreeCAD"
    assert isinstance(engine.config, dict)


def test_freecad_engine_with_config():
    """Test that FreeCAD engine accepts configuration."""
    config = {"freecad_app": "/usr/bin/freecad", "out_formats": "STL,PNG,DXF"}
    engine = EngineFreeCAD(config=config)
    assert engine.config == config


def test_openscad_engine_creation():
    """Test that OpenSCAD engine can be created."""
    engine = EngineOpenSCAD()
    assert engine.engine_name == "OpenSCAD"
    assert isinstance(engine.config, dict)


def test_openscad_engine_with_config():
    """Test that OpenSCAD engine accepts configuration."""
    config = {"openscad_app": "/usr/bin/openscad"}
    engine = EngineOpenSCAD(config=config)
    assert engine.config == config


@pytest.mark.ci_exclude
def test_engine_build_mixed_list():
    """Test that Engine can build a mixed list of parts and assemblies."""
    engine = EngineOpenSCAD()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a part JSON
        part_dir = tmppath / "test_part"
        part_dir.mkdir()
        part_json = part_dir / "test_part.json"
        part_data = {
            "name": "test_part",
            "features": [
                {
                    "name": "cube",
                    "type": "cuboid",
                    "action": "add",
                    "side": "BOTTOM",
                    "x": 0.0,
                    "y": 0.0,
                    "z": 0.0,
                    "x_size": 10,
                    "y_size": 10,
                    "z_size": 10,
                    "center": False,
                }
            ],
            "subtract": [],
        }
        part_json.write_text(json.dumps(part_data))

        # Create an assembly JSON
        assembly_json = tmppath / "test_assembly.json"
        assembly_data = {
            "name": "test_assembly",
            "parts": [
                {
                    "name": "test_part",
                    "x": 0,
                    "y": 0,
                    "z": 0,
                    "rotate": [],
                    "x_size": 10,
                    "y_size": 10,
                    "z_size": 10,
                    "colour": [1.0, 0.5, 0.0],
                    "hash": "",
                }
            ],
        }
        assembly_json.write_text(json.dumps(assembly_data))

        # Build both
        artifacts = engine.build_bulk([part_json, assembly_json])

        # Should have generated some artifacts
        assert isinstance(artifacts, list)


def test_freecad_engine_build_part_no_features():
    """Test FreeCAD engine handling of part with no features."""
    engine = EngineFreeCAD()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        part_dir = tmppath / "empty_part"
        part_dir.mkdir()
        part_json = part_dir / "empty_part.json"
        part_data = {"name": "empty_part", "features": []}
        part_json.write_text(json.dumps(part_data))

        # Should return empty list for part with no features
        artifacts = engine.build_part(part_json)
        assert artifacts == []


def test_freecad_engine_build_assembly_no_parts():
    """Test FreeCAD engine handling of assembly with no parts."""
    engine = EngineFreeCAD()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        assembly_json = tmppath / "empty_assembly.json"
        assembly_data = {"name": "empty_assembly", "parts": []}
        assembly_json.write_text(json.dumps(assembly_data))

        # Should return empty list for assembly with no parts
        artifacts = engine.build_assembly(assembly_json)
        assert artifacts == []


def test_openscad_engine_build_part_no_features():
    """Test OpenSCAD engine handling of part with no features."""
    engine = EngineOpenSCAD()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        part_dir = tmppath / "empty_part"
        part_dir.mkdir()
        part_json = part_dir / "empty_part.json"
        part_data = {"name": "empty_part", "features": []}
        part_json.write_text(json.dumps(part_data))

        # Should return empty list for part with no features
        artifacts = engine.build_part(part_json)
        assert artifacts == []


def test_openscad_engine_build_assembly_no_parts():
    """Test OpenSCAD engine handling of assembly with no parts."""
    engine = EngineOpenSCAD()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        assembly_json = tmppath / "empty_assembly.json"
        assembly_data = {"name": "empty_assembly", "parts": []}
        assembly_json.write_text(json.dumps(assembly_data))

        # Should return empty list for assembly with no parts
        artifacts = engine.build_assembly(assembly_json)
        assert artifacts == []
