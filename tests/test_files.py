import json

from cycax.cycad import Assembly, SheetMetal

# Test some of the file operations.


def test_save(tmp_path):
    """Test save on assembly and parts."""

    assert len(tuple(tmp_path.glob("*"))) == 0, "Test directory should be empty"
    assembly = Assembly("assembly-test")
    mypart1 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="part-test1")
    mypart2 = SheetMetal(x_size=2, y_size=2, z_size=2, part_no="part-test2")
    assembly.add(mypart1)
    assembly.add(mypart2)
    assembly.save(tmp_path)
    assert len(tuple(tmp_path.glob("*"))) > 3, "Expect a directory per part and files for Assembly"
    for i in range(1, 3):
        part_expected_path = tmp_path / f"part-test{i}"
        assert part_expected_path.is_dir(), "Directory for part should exists"
        json_file = part_expected_path / f"part-test{i}.json"
        assert json_file.exists(), "JSON file for part should exists"
        json.loads(json_file.read_text())
