# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import hashlib
from pathlib import Path


def load_file_hash(filename: Path) -> str:
    """Load the stored hash for filename.

    Args:
        filename: The file who's stored hash we need to retrieve.

    Returns:
        The SHA265 hash in hexadesimal format of the contents of the previous version of filename.
    """
    hash_file = filename.parent / f".{filename.name}.hash"
    if hash_file.exists():
        return hash_file.read_text()
    else:
        return "."


def store_file_hash(filename: Path, new_hash: str):
    """Store the hash value that represents the contents of filename.

    Use load_file_hash to fetch the hash for filename.

    Args:
        filename: Store the hash value of this file.
    """
    hash_file = filename.parent / f".{filename.name}.hash"
    hash_file.write_text(new_hash)


def generate_file_hash(filename: Path) -> str:
    """
    Args:
        filename: A SHA256 hash will be generated from the contents of this file.
    Returns:
        A SHA256 hash in hexadesimal format.
    """
    content = filename.read_text()
    hash_value = hashlib.sha256(content.encode("UTF-8")).hexdigest()
    return hash_value


def check_source_hash(source_filepath: Path, target_filepath: Path) -> bool:
    """Check if we should build the target file.

    Args:
        source_filepath: The source file, this file must exists.
        target_filepath: The target file, this is the file we want to find out iof we should create it.
    Returns:
        True if the source file should be generated.
    """
    if not source_filepath.exists():
        msg = f"Cannot create {target_filepath} the source file {source_filepath} does not exists."
        raise ValueError(msg)

    new_hash = generate_file_hash(source_filepath)

    if target_filepath.exists():
        old_hash = load_file_hash(source_filepath)
        # logging.debug("File %s has old hash %s and new hash %s", source_filepath, old_hash, new_hash)
        if old_hash == new_hash:
            return False

    store_file_hash(source_filepath, new_hash)
    return True
