"""Function to help run the model creation."""

import importlib
import importlib.util
import json
import logging
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any

import typer
import xxhash
from rich.logging import RichHandler

from cycax.cli import (
    cmd_build,
    cmd_config,
)
from cycax.cli.config import Settings

FUNCTION_NAMES = [
    "assemble",
    "parts",
    "cycax_assemble",
    "cycax_parts",
    "cycax_part",
]  # TODO: Decide on these, maybe only support cycax_ prefixes.


def run_function(file_path: Path, function_name: str | None = None) -> Path:
    try:
        spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if function_name is None:
            for _function_name in FUNCTION_NAMES:
                if hasattr(module, _function_name):
                    function_name = _function_name
                    break
        if function_name is None:
            logging.error("No function found in file %s, looked for %s", file_path, FUNCTION_NAMES)
            raise typer.Exit(code=1)
        elif not hasattr(module, function_name):
            logging.error("Error finding function %s in file %s", function_name, file_path)
            raise typer.Exit(code=1)

        function = getattr(module, function_name)
        result = function()
        return result
    except Exception as error:
        logging.error("Error running function %s from file %s: %s", function_name, file_path, error)
        raise typer.Exit(code=1) from error


def run_compile(filename: Path, function_name: str | None = None, build_dir: Path = Path("./build")):
    files = []
    cycax_build = run_function(filename, function_name)
    if not isinstance(cycax_build, list):
        cycax_build = [cycax_build]

    for build in cycax_build:
        # TODO: Check the type
        build_file = build.save(build_dir)
        files.append(build_file)

    return files


def cmd_input_scrubber(filename: Path | str, build_dir: Path | str | None = None) -> dict[str, str | Path]:
    if ":" in filename:
        filename, function_name = filename.split(":", 1)
    else:
        function_name = None
    _filename = Path(filename).expanduser().resolve().absolute()
    if not _filename.exists():
        msg = f"File {_filename} does not exist."
        raise FileNotFoundError(msg)
    if build_dir is None:
        build_path = _filename.parent
    else:
        build_path = Path(build_dir).expanduser().resolve().absolute()
    return {"filename": _filename, "build_dir": build_path, "function_name": function_name}


def add_to_build_order(json_file: Path, build_order: dict, level: int = 100):
    _json_file = json_file.expanduser().resolve().absolute()
    if not _json_file.exists():
        logging.error("The file %s does not exist.", _json_file)
        raise typer.Exit(code=1)

    data = json.loads(_json_file.read_text())
    data_hash = xxhash.xxh64(json.dumps(data)).hexdigest()
    if data_hash not in build_order:
        build_order[data_hash] = {
            "index": level,
            "hash": data_hash,
            "path": _json_file,
        }
        for part in data.get("parts", []):
            _part_json = _json_file.parent / part["part_no"] / f"{part['part_no']}.json"
            add_to_build_order(_part_json, build_order, level - 1)
    else:
        build_order[data_hash]["index"] -= 1


def make_build_map(filename: Path | str, build_dir: Path | str | None = None) -> dict:
    json_files = []
    fields = cmd_input_scrubber(filename, build_dir)
    if fields["filename"].suffix == ".py":
        json_files = run_compile(
            filename=fields["filename"], function_name=fields["function_name"], build_dir=fields["build_dir"]
        )
    elif fields["filename"].suffix == ".json":
        json_files = [fields["filename"]]
    elif fields["filename"].is_dir():
        json_files = [Path(f) for f in fields["filename"].iterdir() if f.suffix == ".json"]
    else:
        logging.error("The path %s is not a Python file, JSON file, or directory.", filename)
        raise typer.Exit(code=1)

    build_order = defaultdict(dict)
    for json_file in json_files:
        add_to_build_order(json_file, build_order)

    # TODO: For more complex cases we should consider making this a graph.
    return dict(build_order)
