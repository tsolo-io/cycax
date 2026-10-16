# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Function to help run the model creation."""

import logging
import re
import shutil
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import orjson
import typer
import xxhash
from rich.console import Console

from cycax.cycad import Assembly, CycadPart
from cycax.targets import load_targets


class CycaxCompiler:
    """A compiler for Cycax files.

    Attributes:
        parts: A dictionary of parts.
        root_path: The root path.
        cache_path: The cache path.
        src_json: A list of JSON files used as the source of the build.
        src_py: The Python sources (file or module paths) with CyCAx targets to build.
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
        self.src_py: list[dict] = []

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
        _data = orjson.dumps(data)
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

        if old_hash == _data_hash and json_file_path.exists():
            self.parts[path]["build"] = False
            return

        # Data changed. Write the JSON before the hash, so an interrupted write is retried.
        json_file_path.write_text(_data.decode())
        file_path.write_text(_data_hash)
        self.parts[path]["build"] = True

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
        for src in self.src_py:
            targets = load_targets(src["source"], src["target_name"])
            if not targets:
                logging.debug("No CyCAx targets in %s", src["source"])
            for target in targets:
                logging.info("Compiling %s %s from %s", target.kind, target.name, src["source"])
                for build in target.make():
                    if isinstance(build, Assembly):
                        self.save_assembly(build, self.root_path)
                    else:
                        self.save_part(build, self.root_path)

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
        """Add a source to the build process.

        Args:
            filename: A Python file, JSON file, directory or dotted Python module path. A Python
                source can select one CyCAx target with a `:name` suffix, e.g. `bend2.py:bracket`.
        """
        if ":" in filename:
            filename, target_name = filename.split(":", 1)
        else:
            target_name = None
        self.add_src_path(filename, target_name)

    def add_src_path(self, filename: str | Path, target_name: str | None = None):
        """Add a source to the build process.

        Args:
            filename: A Python file, JSON file, directory or dotted Python module path.
            target_name: The name of the one CyCAx target to build from a Python source.
        """
        _filename = Path(filename).expanduser().resolve().absolute()
        if not _filename.exists():
            if re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", str(filename)):
                # Not a path, so a module path like cycax_parts.powersupplies.meanwell.
                self.src_py.append({"source": str(filename), "target_name": target_name})
                return
            msg = f"File {_filename} does not exist."
            raise FileNotFoundError(msg)

        if _filename.suffix == ".py":
            self.src_py.append({"source": _filename, "target_name": target_name})
        elif _filename.suffix == ".json":
            self.src_json.append({"filename": _filename})
        elif _filename.is_dir():
            for file_path in sorted(_filename.iterdir()):
                if file_path.is_file() and file_path.suffix in (".py", ".json") and not file_path.name.startswith("_"):
                    self.add_src_path(file_path)
        else:
            logging.error("The path %s is not a Python file, JSON file, or directory.", filename)
            raise typer.Exit(code=1)


def compile_or_exit(compiler: CycaxCompiler):
    """Compile, on any error print the traceback and exit with a non-zero code."""
    try:
        compiler.compile()
    except Exception:
        Console(stderr=True).print_exception()
        raise typer.Exit(code=1) from None
