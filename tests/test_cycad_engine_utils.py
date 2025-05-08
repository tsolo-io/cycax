# Tests for the utilities of from CyCAD engines.
from cycax.cycad.engines.utils import check_source_hash


def test_check_source_hash(tmp_path):
    source_test_file = tmp_path / "mypart.json"
    target_test_file = tmp_path / "mypart.3d"
    hash_test_file = tmp_path / ".mypart.json.hash"
    assert not source_test_file.exists(), "There should be no source file."
    assert not target_test_file.exists(), "There should be no target file."
    assert not hash_test_file.exists(), "There should be no hash file."
    source_test_file.write_text("bla bla")
    # No hash file and no target file, expect True.
    assert check_source_hash(source_test_file, target_test_file), (
        "Should create the target since it is not there and there is no source hash file."
    )
    assert hash_test_file.exists(), "The hash file should be there."
    # No target file, expect True.
    assert check_source_hash(source_test_file, target_test_file), "Should create the target since it is not there."
    target_test_file.write_text("yes")
    # Target exists file and no update to source, expect False.
    assert not check_source_hash(source_test_file, target_test_file), "Should NOT create the target."
    hash_test_file.write_text("1")
    assert check_source_hash(source_test_file, target_test_file), "Should create the target since hash is different."
