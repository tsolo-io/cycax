"""Filesystem utility functions."""

import logging
from pathlib import Path


def get_directory_stat(directory: Path | str) -> dict[str, int]:
    """Calculate the total size (in bytes), access time, and creation time of a directory.

    This function recursively walks through all files in the directory
    and its subdirectories, summing up their stats.

    Args:
        directory: The path to the directory (can be Path or string).

    Returns:
        The total size of the directory in bytes, the last access time, and the earliest creation time.

    Raises:
        FileNotFoundError: If the directory doesn't exist.
        NotADirectoryError: If the path exists but is not a directory.

    Example:
        >>> size = get_directory_size("/path/to/directory")
        >>> print(f"Directory size: {size / (1024**2):.2f} MB")
    """
    dir_path = Path(directory).expanduser().resolve().absolute()

    if not dir_path.exists():
        msg = f"Directory {dir_path} does not exist."
        raise FileNotFoundError(msg)

    if not dir_path.is_dir():
        msg = f"Path {dir_path} is not a directory."
        raise NotADirectoryError(msg)

    total_size = 0

    atime = []
    ctime = []
    try:
        for item in dir_path.rglob("*"):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                    atime.append(item.stat().st_atime)
                    ctime.append(item.stat().st_ctime)
                except (PermissionError, OSError) as error:
                    logging.warning("Cannot access file %s: %s", item, error)
                    continue
    except PermissionError as error:
        logging.error("Permission denied while accessing directory %s: %s", dir_path, error)
        raise

    return {"size": total_size, "atime": max(atime), "ctime": min(ctime)}


def get_all_subdirectory_stats(directory: Path | str) -> dict[Path, dict[str, int]]:
    """Get the size, atime, and ctime of all immediate subdirectories in the given path.

    This function calculates a summary of each subdirectory (including
    all nested files and subdirectories within it).

    Args:
        directory: The path to the parent directory (can be Path or string).

    Returns:
        A dictionary mapping each subdirectory path to its total size in bytes, access time, and creation time.

    Raises:
        FileNotFoundError: If the directory doesn't exist.
        NotADirectoryError: If the path exists but is not a directory.
    """
    dir_path = Path(directory).expanduser().resolve().absolute()

    if not dir_path.exists():
        logging.error("Directory %s does not exist.", dir_path)
        return {}

    if not dir_path.is_dir():
        msg = f"Path {dir_path} is not a directory."
        raise NotADirectoryError(msg)

    subdirectory_sizes = {}

    try:
        for item in dir_path.iterdir():
            if item.is_dir():
                subdirectory_sizes[item] = get_directory_stat(item)
    except PermissionError as error:
        logging.error("Permission denied while accessing directory %s: %s", dir_path, error)
        raise

    return subdirectory_sizes


def format_size(size_bytes: int) -> str:
    """Format a size in bytes to a human-readable string.

    Args:
        size_bytes: The size in bytes.

    Returns:
        A human-readable string representation of the size.

    Example:
        >>> format_size(1024)
        '1.00 KB'
        >>> format_size(1536)
        '1.50 KB'
        >>> format_size(1048576)
        '1.00 MB'
    """
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


def guess_name_cache_directory_name(path: Path) -> str:
    """Guess a name for a file or directory based on its path.

    For a directory we see if there is a file with a .json extension and use this file name as the folder name.
    Args:
        path: The path to the file or directory.

    Returns:
        A guessed name for the file or directory.
    """
    if path.is_file():
        return path.stem
    elif path.is_dir():
        for file in path.iterdir():
            if file.suffix == ".json":
                return file.stem
        return path.stem
    else:
        msg = f"Path {path} is neither a file nor a directory."
        raise ValueError(msg)
