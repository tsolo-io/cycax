import hashlib
from pathlib import Path
def hex_code_check(tmp_path: Path, filename: str, ext: str, hex_code: str):
    """This method is used to produce hash codes of the desired files."""

    filename = tmp_path / filename / f"{filename}{ext}"

    content = filename.read_text()
    hash_value_file = hashlib.sha256(content.encode("UTF-8")).hexdigest()
    
    assert hash_value_file == hex_code