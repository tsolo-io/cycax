# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path


class PartEngine:
    """Base Class for all PartEngines.

    Attributes:
        name: Name of the part.
        path: The path where the assembly is stored.
            Default to current working directory.
            The part is stored in a directory matching it name in this path.
        config: Engine specific configuration.
    """

    def __init__(self, name: str | None = None, path: Path | None = None, config: dict | None = None):
        self._base_path = None
        self._json_file = None
        self.name = name
        self.part_no = name  # TODO: Deprecate self.part_no
        self.config = dict(config or {})
        if path:
            self.set_path(path)
        self.check_part_init()

    def check_part_init(self):
        """Early hook for part classes to do custom checks."""
        pass

    def new(self, name: str, path: Path):
        self.name = name
        self.set_path(path)

    def set_path(self, path: Path):
        if path is None:
            path = Path(".")
        if not path.exists():
            logging.error("Engine using a path that does not exists. Path=%s", path)
        self._base_path = path
        name = self.name
        self._json_file = self._base_path / name / f"{name}.json"
        if not self._json_file.exists():
            raise FileNotFoundError(self._json_file)

    def get_appimage(self, name) -> Path | None:
        paths = ["~/Applications", self._base_path]
        appimage = None
        for p in paths:
            path = Path(p).expanduser()
            if not path.exists():
                # There is no such path.
                logging.error("No path %s", path)
                break
            for appimg in path.glob(f"{name}*.AppImage"):
                # Very simple implementation to get tests to pass on CI.
                # TODO: Sort the Appimages and to get the latest.
                appimage = appimg
        return appimage

    def create(self, part):
        pass

    def build(self, part):
        msg = "The build method needs to be implemented for this engine."
        raise NotImplementedError(msg)

    def file_list(self, files: list, engine: str, score: int) -> list:
        """Generate a list of artefacts/files."""
        model_files = []
        for _file in files:
            filepath = _file["file"]
            if filepath.exists():
                _file["type"] = filepath.suffix.strip(".").upper()
                _file["engine"] = engine
                _file["score"] = score
                model_files.append(_file)
        return model_files
