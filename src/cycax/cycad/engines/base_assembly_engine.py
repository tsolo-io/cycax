import logging
from pathlib import Path


class AssemblyEngine:
    """ """

    def __init__(self, name, path: Path = None, config: dict = None):
        self._base_path = None
        self._json_file = None
        self.name = name
        self.config = {} if config is None else config
        self.set_path(path)

    def set_path(self, path: Path):
        if path is None:
            path = Path(".")
        if not path.exists():
            logging.error("Engine using a path that does not exists. Path=%s", path)
        self._base_path = path
        name = self.name
        self._json_file = self._base_path / (name + ".json")
        if not self._json_file.exists():
            raise FileNotFoundError(self._json_file)
