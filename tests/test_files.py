import json
from pathlib import Path

from cycax.cycad import Assembly, SheetMetal

# Test some of the file operations.


def check_json_file(dir_path: Path, name: str):
    json_file = dir_path / f"{name}.json"
    assert json_file.exists(), "JSON file should exists"
    json.loads(json_file.read_text())


def check_files(dir_path: Path, name: str, file_extensions: list[str]):
    for ext in file_extensions:
        file_path = dir_path / f"{name}.{ext}"
        assert file_path.exists(), "File should exists"


def test_save(tmp_path):
    """Test save on assembly and parts."""

    assert len(tuple(tmp_path.glob("*"))) == 0, "Test directory should be empty"
    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="part-test1")
    mypart2 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="part-test2")
    assembly.add(mypart1)
    assembly.add(mypart2)
    assembly.save(tmp_path)
    assert len(tuple(tmp_path.glob("*"))) > 2, "Expect a directory per part and files for Assembly"
    check_json_file(tmp_path, "assembly_test")
    for i in range(1, 3):
        part_expected_path = tmp_path / f"part_test{i}"
        assert part_expected_path.is_dir(), "Directory for part should exists"
        check_json_file(part_expected_path, f"part_test{i}")


def test_render_assembly_openscad(tmp_path):
    """Test render on assembly and parts."""

    assert len(tuple(tmp_path.glob("*"))) == 0, "Test directory should be empty"
    assembly = Assembly("assembly_test")
    parts = {}
    for part in ["partA", "partB", "partC", "partD", "partE", "partF"]:
        mypart = SheetMetal(x_size=2, y_size=2, z_size=2, part_no=part)
        assembly.add(mypart)
        parts[part] = mypart
    # TODO: Rotate and level parts.
    assembly.save(tmp_path)
    assembly.render(engine="OpenSCAD")

    assert len(tuple(tmp_path.glob("*"))) > len(parts.keys()), "Expect a directory per part and files for Assembly"
    check_files(tmp_path, "assembly_test", ["json", "scad"])
    for part in parts.keys():
        part_expected_path = tmp_path / part.strip().replace("-", "_").lower()
        assert part_expected_path.is_dir(), "Directory for part should exists"
        check_files(part_expected_path, part.strip().replace("-", "_").lower(), ["json", "scad", "stl"])


def test_render_part_freecad(tmp_path):
    """Test render a part with FreeCAD."""

    assert len(tuple(tmp_path.glob("*"))) == 0, "Test directory should be empty"
    assembly = Assembly("assembly_test")
    parts = {}
    for part in ["part_A"]:
        mypart = SheetMetal(x_size=2, y_size=2, z_size=2, part_no=part)
        assembly.add(mypart)
        parts[part] = mypart
    # TODO: Rotate and level parts.
    assembly.save(tmp_path)
    assembly.render(engine="OpenSCAD", part_engine="FreeCAD")

    assert len(tuple(tmp_path.glob("*"))) > len(parts.keys()), "Expect a directory per part and files for Assembly"
    check_files(tmp_path, "assembly_test", ["json", "scad"])
    for part in parts.keys():
        part_expected_path = tmp_path / part.strip().replace("-", "_").lower()
        assert part_expected_path.is_dir(), "Directory for part should exists"
        check_files(part_expected_path, part.strip().replace("-", "_").lower(), ["json", "FCStd"])
