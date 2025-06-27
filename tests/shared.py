# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
import json
from pathlib import Path


def check_json_reference(json_file: Path, reference_file: str) -> bool:
    """Check if a JSON file matches a reference file.

    Args:
        json_file: Path to the JSON file to check.
        reference_file: Path to the reference JSON file.

    Returns:
        True if the files are equal, False otherwise.
    """
    dut = json.loads(json_file.read_text())
    ref = json.loads((Path("./tests/references") / reference_file).read_text())
    assert dut == ref, f"Data under test from {json_file} does not match reference"


def check_stl_reference(stl_file: Path, reference_file: str) -> bool:
    """Check if an STL file matches a reference file.

    Args:
        stl_file: Path to the STL file to check.
        reference_file: Path to the reference STL file.

    Returns:
        True if the files are equal, False otherwise.
    """
    assert stl_compare(stl_file, Path("./tests/references") / reference_file)


def stl_compare(file1: Path, file2: Path) -> bool:
    """Compare two STL files for equality.

    This is a very memory intensive operation and should be used sparingly.

    Args:
        file1: Path to the first STL file.
        file2: Path to the second STL file.

    Returns:
        True if the files are equal, False otherwise.
    """
    lines1 = file1.read_text().splitlines()
    lines2 = file2.read_text().splitlines()
    if len(lines1) != len(lines2):
        return False
    sorted_lines1 = sorted(lines1)
    sorted_lines2 = sorted(lines2)
    for line_number in range(len(lines1)):
        if sorted_lines1[line_number] != sorted_lines2[line_number]:
            return False
    return True


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


def hex_code_check(
    tmp_path: Path,
    filename: str,
    ext: str,
    hex_code: str | None = None,
    hex_codes: list[str] | None = None,
    *,
    return_hex=False,
    equal=True,
) -> str:
    """This method is used to produce hash codes of the desired files."""

    filename = tmp_path / filename / f"{filename}{ext}"
    hash_value_file = get_file_hash(filename)

    if return_hex:
        return hash_value_file
    elif hex_code:
        if equal:
            assert hash_value_file == hex_code, f"The hash value of the file is {hash_value_file} but expect {hex_code}"
        else:
            assert hash_value_file != hex_code, f"The hash value of the file is {hash_value_file}, this is incorrect."
    elif hex_codes:
        if equal:
            assert hash_value_file in hex_codes, (
                f"The hash value of the file is {hash_value_file}, expected it to be one of {hex_codes}."
            )
        else:
            assert hash_value_file not in hex_codes, (
                f"The hash value of the file is {hash_value_file}, not supposed to be one of {hex_codes}."
            )

    return ""
