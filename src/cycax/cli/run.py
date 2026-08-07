# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Function to help run the model creation."""

import importlib
import importlib.util
import logging
import re
import shutil
from collections import defaultdict, namedtuple
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import orjson
import typer
import xxhash

from cycax.cycad import Assembly, CycadPart

BuildTarget = namedtuple("BuildTarget", ["name", "path", "type", "obj"])

FUNCTION_NAMES = [
    "assemble",
    "parts",
    "cycax_assemble",
    "cycax_parts",
    "cycax_part",
]  # TODO: Decide on these, maybe only support cycax_ prefixes.


def run_function(file_path: Path, function_name: str | None = None) -> Path | None:
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
            return None
        elif not hasattr(module, function_name):
            logging.error("Error finding function %s in file %s", function_name, file_path)
            return None

        function = getattr(module, function_name)
        result = function()
        return result
    except Exception as error:
        logging.error("Error running function %s from file %s: %s", function_name, file_path, error)
        return None


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
            "path": json_file,
        }
        for part in data.get("parts", []):
            _part_json = json_file.parent / part["name"] / f"{part['name']}.json"
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
    """A compiler for Cycax files.

    Attributes:
        parts: A dictionary of parts.
        root_path: The root path.
        cache_path: The cache path.
        src_json: A list of JSON files used as the source of the build.
        src_py: A list of Python files used as the source of the build.
    """

    def __init__(self, root_build_dir: Path, cache_dir: Path, settings: dict):
        self.settings = settings
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
        """Join a path with a normalised name.

        The name is normalised, slugified, by replacing all non-word characters with underscores and
        converting to lowercase.

        Args:
            base_path: The base path.
            name: The name to join.

        Returns:
            The joined path.
        """
        _name = re.sub(r"\W", "_", name.strip(), flags=re.ASCII).lower()
        return Path(base_path) / _name

    def save_json(self, path: Path, name: str, data: dict | list, index: int = 100):
        """Save the data to a JSON file and check if the contents changed.

        Args:
        path: The directory path where the JSON file will be saved.
        name: The name of the JSON file.
        data: The data to be saved as JSON.
        """
        path.mkdir(parents=True, exist_ok=True)
        json_file_path = path / f"{name}.json"
        _data = orjson.dumps(data).decode()
        _data_hash = xxhash.xxh64(_data).hexdigest()
        self.parts[path]["path"] = path
        self.parts[path]["definition_file"] = json_file_path
        self.parts[path]["name"] = name
        self.parts[path]["hash"] = _data_hash
        self.parts[path]["index"] = min(self.parts[path].get("index", 100), index)

        file_path = path / ".id"
        old_hash = ""
        if file_path.exists():
            old_hash = file_path.read_text()

        if old_hash == _data_hash:
            self.parts[path]["build"] = False
            return

        # Data changed.
        file_path.write_text(_data_hash)
        self.parts[path]["build"] = True

        json_file_path.write_text(_data)
        logging.info("Saved %s definition to %s with hash %s", name, json_file_path, _data_hash)

    def load_json(self, path: Path, index: int = 1):
        """Load a JSON file.

        Args:
            path: The path to the JSON file.
            index: The index of the JSON file. Defaults to 1.
        """
        if not path.exists():
            msg = f"File {path} does not exist"
            raise FileNotFoundError(msg)
        data = orjson.loads(path.read_text())
        _data = orjson.dumps(data).decode()
        _data_hash = xxhash.xxh64(_data).hexdigest()
        self.parts[path]["path"] = path.parent
        self.parts[path]["definition_file"] = path
        self.parts[path]["name"] = data["name"]
        self.parts[path]["hash"] = _data_hash
        self.parts[path]["build"] = True
        self.parts[path]["index"] = max(index, self.parts[path].get("index", 1))
        self.parts[path]["assembly"] = False
        file_path = path.parent / ".id"
        old_hash = ""
        if file_path.exists():
            old_hash = file_path.read_text()

        if old_hash == _data_hash:
            self.parts[path]["build"] = False

        # If this is an assembly we need to load the parts.
        if "parts" in data:
            self.parts[path]["assembly"] = True
            for part in data["parts"]:
                name = part["name"]
                _path = path.parent / name / f"{name}.json"
                self.load_json(_path, index=index + 4)

    def save_part(self, part: CycadPart, path: Path, index: int = 1):
        """Save a part to a JSON file.

        Args:
            part: The part to save.
            path: The path to save the part to.
            index: The index of the part. Defaults to 1.
        """
        _build_path = self.path_join(path, part.part_no)
        self.save_json(_build_path, part.part_no, part.export(), index=index)
        self.parts[_build_path]["assembly"] = False

    def save_assembly(self, assembly: Assembly, path: Path, index: int = 1):
        """Save an assembly to a JSON file.

        Args:
            assembly: The assembly to save.
            path: The path to save the assembly to.
            index: The index of the assembly. Defaults to 1.
        """
        _build_path = self.path_join(path, assembly.name)
        for part in assembly.parts.values():
            if isinstance(part, Assembly):
                self.save_assembly(part, _build_path, index=index + 1)
            elif isinstance(part, CycadPart):
                self.save_part(part, _build_path, index=index + 4)
            else:
                logging.error("The assembly build process returned an unexpected type: %s %s", type(part), part)

        self.save_json(_build_path, assembly.name, assembly.export(), index=index)
        self.parts[_build_path]["assembly"] = True

    def compile(self):
        """Compile the source files (Python) into a CyCAx JSON file."""
        # Do the CyCAx build for every discovered Python file.
        for py_file in self.src_py:
            cycax_build = run_function(py_file["filename"], py_file["function_name"])
            if cycax_build is None:
                continue
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

    def build_order(self) -> Iterable[dict[str, Any]]:
        """Return parts in the order they should be built.

        The order is determined by the 'index' key in the part's metadata.
        If 'index' is not present, the part is considered to have an index of 100.
        Index was created as the parts were added.

        Returns:
            Parts in the order they should be built.
        """
        yield from sorted(self.parts.values(), key=lambda part: part.get("index", 100), reverse=True)

    def check_cache(self, cache_id: str) -> bool:
        """Check if the cache exists for the given hash.

        Args:
            hash: The hash of the part.

        Returns:
            True if the cache exists, False otherwise.
        """
        return self.cache_path.joinpath(cache_id).exists()

    def from_cache(self, part: dict) -> bool:
        """Load a part from the cache.

        Args:
            part: The part to load.

        Returns:
            True if the part was loaded from the cache, False otherwise.
        """
        # Load the part from the cache here
        cache_path = self.cache_path.joinpath(part["hash"])
        if not cache_path.exists():
            return False
        loaded_from_cache = False
        for file in cache_path.iterdir():
            if file.suffix == ".json" or file.name.startswith("."):
                continue
            shutil.copy(file, part["path"])
            loaded_from_cache = True
        return loaded_from_cache

    def to_cache(self, part: dict[str, Any]):
        """Save a part to the cache.

        Args:
            part: The part to save.
        """
        # Save the part to the cache here
        cache_path = self.cache_path.joinpath(part["hash"])
        cache_path.mkdir(parents=True, exist_ok=True)
        for file in part["path"].iterdir():
            if file.is_dir():
                continue
            shutil.copy(file, cache_path)

    def build_part(self, part: dict):
        """Build a part.

        Args:
            part: The part to build.
        """
        # Build the part here
        _filename = part["path"] / f"{part['name']}.json"
        if "assembly" not in part:
            msg = "Invalid part"
            raise ValueError(msg)
        if not part["assembly"]:
            from cycax.cycad.engines.part_freecad import (  # noqa PLC0415 Import here to make CLI faster
                PartEngineFreeCAD,
                bulk_build,
            )

            engine = PartEngineFreeCAD(name=part["name"], path=part["path"].parent)
            engine._json_file = _filename
            engine.build(None)

            bulk_build()

    def build(self):
        """Build using the CyCAx JSON files into CAD models."""
        for json_file in self.src_json:
            # If there are any JSON files that needs to be loaded, load them.
            self.load_json(json_file["filename"])

        # Loop through the build order and build the parts.
        from cycax.cycad.engines.part_freecad import bulk_build  # noqa PLC0415 Import here to make CLI faster

        write_back_to_cache = []
        freecad_list = []
        for part in self.build_order():
            if not self.from_cache(part):
                write_back_to_cache.append(part)
                if not part["assembly"]:
                    _filename = part["path"] / f"{part['name']}.json"
                    freecad_list.append(str(_filename))
                # self.build_part(part)
                # self.to_cache(part)

        if freecad_list:
            bulk_build(app_bin=self.settings["freecad_app"], path=self.settings["build_directory"], parts=freecad_list)

        for part in write_back_to_cache:
            self.to_cache(part)

    def add_src(self, filename: str):
        """Add a source file to the build process.

        Args:
            filename: The filename of the source file. Could contain reference to a function.
        """
        if ":" in filename:
            filename, function_name = filename.split(":", 1)
        else:
            function_name = None
        self.add_src_path(filename, function_name)

    def add_src_path(self, filename: str, function_name: str | None = None):
        """Add a source file to the build process.

        Args:
            filename: The filename of the source file.
            function_name: The name of the function to be called from the source file.
        """
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
                if file_path.is_file() and file_path.suffix in (".py", ".json") and not file_path.name.startswith("_"):
                    self.add_src_path(file_path)
        else:
            logging.error("The path %s is not a Python file, JSON file, or directory.", filename)
            raise typer.Exit(code=1)
