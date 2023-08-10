import hashlib
from pathlib import Path


def get_file_hash(filename: str) -> str:
    """Calculate the sha256 of a file.

    Args:
        filename: Name of the file to read and calculate hash.

    Returns:
        The SHA256 value that represents the files contents as a hexadecimal string.
    """
    content = filename.read_text()
    hash_value_file = hashlib.sha256(content.encode("UTF-8")).hexdigest()
    return hash_value_file


def hex_code_check(tmp_path: Path, filename: str, ext: str, hex_code: str = "", return_hex=False, equal=True):
    """This method is used to produce hash codes of the desired files."""

    filename = tmp_path / filename / f"{filename}{ext}"
    hash_value_file = get_file_hash(filename)

    if return_hex:
        return hash_value_file
    else:
        print(f"Got {hash_value_file} expect {hex_code}")
        if equal:
            assert hash_value_file == hex_code
        else:
            assert hash_value_file != hex_code
        return ""
