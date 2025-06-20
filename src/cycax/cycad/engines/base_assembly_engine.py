# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path


class AssemblyEngine:
    """Base Class for all AssemblyEngines.

    Attributes:
        name: Name of the assembly.
        path: The path where the assembly is stored. Default to current working directory.
        config: Engine specific configuration.
    """

    def __init__(self, name: str | None = None, path: Path | None = None, config: dict | None = None):
        self._base_path = None
        self._json_file = None
        self.config = dict(config or {})
        if name:
            self.set_name(name)
        if path:
            self.set_path(path)
        self.check_assembly_init()

    def check_assembly_init(self):
        """Early hook for assembly classes to do custom checks."""
        pass

    def set_name(self, name: str | None = None):
        if name:
            self.name = name
            self.part_no = name  # TODO: Deprecate self.part_no

    def set_path(self, path: Path):
        if path is None:
            path = Path(".")
        if not path.exists():
            logging.error("Engine using a path that does not exists. Path=%s", path)
        self._base_path = path
        name = self.name
        self._json_file = self._base_path / (name.lower() + ".json")
        if not self._json_file.exists():
            raise FileNotFoundError(self._json_file)

    def build(self):
        msg = "The build method needs to be implemented for this engine."
        raise NotImplementedError(msg)
