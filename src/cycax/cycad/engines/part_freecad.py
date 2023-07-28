import logging
import os
import subprocess
import sys
from pathlib import Path

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.utils import check_source_hash
from cycax.cycad.location import TOP


class PartEngineFreeCAD(PartEngine):
    def build(self) -> dict:
        fcstd_file = self._base_path / self.name / f"{self.name}.FCStd"
        if check_source_hash(self._json_file, fcstd_file):
            app_bin = self.get_appimage("FreeCAD")

            logging.error("Use freeCAD %s", app_bin)
            freecad_py = Path(sys.modules[self.__module__].__file__).parent / "cycax_part_freecad.py"

            out_formats_set = set()
            for file_format in self.config.get("out_formats", []):
                out_formats_set.add(":".join(file_format[:2]))

            environment = dict(os.environ)
            environment.update(
                {
                    "CYCAX_JSON": self._json_file,
                    "CYCAX_CWD": self._base_path,
                    "CYCAX_OUT_FORMATS": ",".join(out_formats_set),
                }
            )
            result = subprocess.run(
                [app_bin, freecad_py],
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

        _files = [
            {"file": self._base_path / self.name / f"{self.name}-FreeCAD.stl"},
            {"file": self._base_path / self.name / f"{self.name}-perspectiveAll.png"},
            {"file": self._base_path / self.name / f"{self.name}-perspective.dxf", "side": TOP},
            {"file": self._base_path / self.name / f"{self.name}-perspectiveTop.png", "side": TOP},
            {"file": self._base_path / self.name / f"{self.name}.FCStd", "description": "FreeCAD primary source file."},
        ]

        return self.file_list(files=_files, engine="FreeCAD", score=5)
