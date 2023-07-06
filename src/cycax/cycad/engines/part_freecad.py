import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.features import nut_specifications
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class PartEngineFreeCAD(PartEngine):
    def build(self) -> dict:
        model_files = {}
        app_bin = self.get_appimage("FreeCAD")

        logging.error("Use freeCAD %s", app_bin)
        freecad_py = Path(sys.modules[self.__module__].__file__).parent / "cycax_part_freecad.py"

        result = subprocess.run([app_bin, freecad_py, self.name, self._base_path], capture_output=True, text=True)

        if result.stdout:
            logging.info("OpenSCAD: %s", result.stdout)
        if result.stderr:
            logging.error("OpenSCAD: %s", result.stderr)

        # raise AssertionError()
        return model_files
