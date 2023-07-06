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

        environment = dict(os.environ)
        environment.update({"CYCAX_JSON": self._json_file, "CYCAX_CWD": self._base_path})
        cmd = [app_bin, freecad_py.absolute()]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=environment,
            shell=False,
        )
        # TODO: Read https://wiki.freecad.org/Start_up_and_Configuration and set logging and headless args.

        if result.stdout:
            logging.info("FreeCAD: %s", result.stdout)
        if result.stderr:
            logging.error("FreeCAD: %s", result.stderr)

        # raise AssertionError()
        return model_files
