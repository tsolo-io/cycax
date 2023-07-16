# Tests for the utilities of from CyCAD engines.
from cycax.cycad.engines.utils import  load_file_hash, store_file_hash, generate_file_hash, check_source_hash

# def load_file_hash(filename: Path) -> str:
# def store_file_hash(filename: Path, new_hash: str):
# def generate_file_hash(filename: Path) -> str:
# def check_source_hash(source_filepath: Path, target_filepath: Path) -> bool:

def test_check_source_hash(tmp_path):

    source_test_file = tmp_path / "mypart.json"
    target_test_file = tmp_path / "mypart.3d"
    hash_test_file = tmp_path / ".mypart.json.hash"
    assert not source_test_file.exists(), "There should be no source file."
    assert not target_test_file.exists(), "There should be no source file."
    assert not hash_test_file.exists(), "There should be no hash file."
    source_test_file.write_text("bla bla")
    # No hash file and no target file, expect True.
    assert check_source_hash(source_test_file, target_test_file), "We should create the target since it is not there and there is no source hash file."
    assert hash_test_file.exists(), "The hash file should be there."
    # No target file, expect True.
    assert check_source_hash(source_test_file, target_test_file), "We should create the target since it is not there."
    target_test_file.write_text("yes")
    # Target exists file and no update to source, expect False.
    assert not check_source_hash(source_test_file, target_test_file), "We should NOT create the target."
