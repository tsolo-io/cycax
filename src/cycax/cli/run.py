"""Function to help run the model creation."""

import importlib
import importlib.util
import json
import logging
import re
from asyncio.unix_events import SelectorEventLoop
from collections import defaultdict, namedtuple
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any

import orjson
import typer
import xxhash
from rich.logging import RichHandler

from cycax.cli import (
    cmd_build,
    cmd_config,
)
from cycax.cli.config import Settings
from cycax.cycad import Assembly, CycadPart

BuildTarget = namedtuple("BuildTarget", ["name", "path", "type", "obj"])

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
        xhash, _ = hash_from_path(build_file)
        logging.info("Saved build file %s %s", xhash, build_file)
        files.append(build_file)

    return files


def cmd_input_scrubber(filename: Path | str, build_dir: Path | str) -> dict[str, str | Path]:
    if ":" in filename:
        filename, function_name = filename.split(":", 1)
    else:
        function_name = None
    _filename = Path(filename).expanduser().resolve().absolute()
    if not _filename.exists():
        msg = f"File {_filename} does not exist."
        raise FileNotFoundError(msg)
    build_path = Path(build_dir).expanduser().resolve().absolute()
    if not build_path.exists():
        logging.warning("Build directory must exists. Please create %s and run the command again.", build_path)
        raise typer.Abort()
    return {"filename": _filename, "build_dir": build_path, "function_name": function_name}


def hash_from_path(json_file: Path) -> tuple[str, Any]:
    _json_file = json_file.expanduser().resolve().absolute()
    if not _json_file.exists():
        logging.error("The file %s does not exist.", _json_file)
        raise typer.Exit(code=1)

    data = orjson.loads(_json_file.read_text())
    data_hash = xxhash.xxh64(orjson.dumps(data)).hexdigest()
    return data_hash, data


def add_to_build_order(json_file: Path, build_order: dict, level: int = 100):
    data_hash, data = hash_from_path(json_file)
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


class CycaxCompiler:
    def __init__(self, root_build_dir: Path, cache_dir: Path):
        self.parts = defaultdict(dict)
        self.root_path = Path(root_build_dir).expanduser().resolve().absolute()
        if not self.root_path.exists():
            logging.warning("Build directory must exists. Please create %s and run the command again.", self.root_path)
            raise typer.Abort()
        self.cache_path = Path(cache_dir).expanduser().resolve().absolute()
        if not self.cache_path.exists():
            self.cache_path.mkdir(parents=True, exist_ok=True)
        self.src_json: list[Path] = []
        self.src_py: list[Path] = []

    def path_join(self, base_path: Path, name: str) -> Path:
        _name = re.sub(r"\W", "_", name.strip(), flags=re.ASCII).lower()
        return Path(base_path) / _name

    def save_json(self, path: Path, name: str, data: dict | list) -> tuple[bool, str]:
        """Save the data to a JSON file and check if the contents changed.

        Args:
        path: The directory path where the JSON file will be saved.
        name: The name of the JSON file.
        data: The data to be saved as JSON.

        Returns:
        A tuple containing a boolean indicating if the contents changed and the hash of the saved data.
        """
        path.mkdir(parents=True, exist_ok=True)
        json_file_path = path / f"{name}.json"
        _data = orjson.dumps(data).decode()
        _data_hash = xxhash.xxh64(_data).hexdigest()
        self.parts[path]["path"] = path
        self.parts[path]["name"] = name
        self.parts[path]["hash"] = _data_hash

        file_path = path / ".id"
        old_hash = ""
        if file_path.exists():
            old_hash = file_path.read_text()

        if old_hash == _data_hash:
            self.parts[path]["build"] = False
            return False, _data_hash

        # Data changed.
        file_path.write_text(_data_hash)
        self.parts[name]["build"] = True

        json_file_path.write_text(_data)
        logging.info("Saved %s to %s with hash %s", name, json_file_path, _data_hash)
        return True, _data_hash

    def load_json(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(f"File {path} does not exist")
        data = orjson.loads(path.read_text())
        _data = orjson.dumps(data).decode()
        _data_hash = xxhash.xxh64(_data).hexdigest()
        self.parts[path]["path"] = path
        self.parts[path]["name"] = data["name"]
        self.parts[path]["hash"] = _data_hash
        self.parts[path]["build"] = True
        file_path = path.parent / ".id"
        old_hash = ""
        if file_path.exists():
            old_hash = file_path.read_text()

        if old_hash == _data_hash:
            self.parts[path]["build"] = False

    def save_part(self, part: CycadPart, path: Path) -> tuple[bool, dict]:
        _build_path = self.path_join(path, part.part_no)
        changed, part.hash = self.save_json(_build_path, part.part_no, part.export())
        build_target = BuildTarget(path=_build_path, name=part.part_no, type="part", obj=part)
        return changed, build_target

    def save_assembly(self, assembly: Assembly, path: Path) -> tuple[bool, dict]:
        changed_items = set()
        _build_path = self.path_join(path, assembly.name)
        for part in assembly.parts.values():
            if isinstance(part, Assembly):
                changed, changed_item = self.save_assembly(part, _build_path)
                if changed:
                    changed_items.union(changed_item)
            elif isinstance(part, CycadPart):
                changed, changed_item = self.save_part(part, _build_path)
                if changed:
                    changed_items.add(changed_item)
            else:
                logging.error("The assembly build process returned an unexpected type: %s %s", type(build), build)

        changed, assembly.hash = self.save_json(_build_path, assembly.name, assembly.export())
        if changed:
            changed_item = BuildTarget(
                path=_build_path,
                name=assembly.name,
                type="assembly",
                obj=assembly,
            )
            changed_items.add(changed_item)
        return changed, changed_items

    def compile(self):
        # Do the CyCAx build for every discovered Python file.
        for py_file in self.src_py:
            cycax_build = run_function(py_file["filename"], py_file["function_name"])
            # The build function can return more than one build
            if not isinstance(cycax_build, list):
                cycax_build = [cycax_build]

            for build in cycax_build:
                if isinstance(build, Assembly):
                    self.save_assembly(build, self.root_path)
                elif isinstance(build, CycadPart):
                    self.save_part(build, self.root_path)
                else:
                    logging.error("The build process returned an unexpected type: %s %s", type(build), build)

    def build(self):
        for json_file in self.src_json:
            self.load_json(json_file["filename"])

    def add_src(self, filename: str):
        if ":" in filename:
            filename, function_name = filename.split(":", 1)
        else:
            function_name = None
        self.add_src_path(filename, function_name)

    def add_src_path(self, filename: str, function_name: str | None = None):
        _filename = Path(filename).expanduser().resolve().absolute()
        if not _filename.exists():
            msg = f"File {_filename} does not exist."
            raise FileNotFoundError(msg)

        if _filename.suffix == ".py":
            self.src_py.append({"filename": _filename, "function_name": function_name})
        elif _filename.suffix == ".json":
            self.src_json.append({"filename": _filename})
        elif _filename.is_dir():
            for file_path in _filename.iterdir():
                if file_path.is_file() and file_path.suffix in (".py", ".json"):
                    self.add_src_path(file_path)
        else:
            logging.error("The path %s is not a Python file, JSON file, or directory.", filename)
            raise typer.Exit(code=1)
