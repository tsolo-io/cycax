# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import subprocess
import sys
from pathlib import Path

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.utils import check_source_hash


class PartEngineFreeCADBend(PartEngine):
    """Builds a `SheetMetalBend` part via the dedicated `FreeCADBend` engine
    (`cycax_part_freecad_bend.py`), using the FreeCAD SheetMetal workbench for real bends
    and unfolding. See docs/content/sheetmetal-bend-design.md.

    Unlike `PartEngineFreeCAD`, output formats aren't configurable: every build produces
    the same four artefacts -- folded STEP, a live/editable FCStd, unfolded STEP, and
    unfolded (layered) DXF -- since that's what a bent sheet-metal part always needs.
    """

    def build(self, part) -> dict:
        if self.name is None:
            self.name = part.part_no
        if self._base_path is None:
            self.set_path(path=part._base_path)
        fcstd_file = self._base_path / self.name / f"{self.name}.FCStd"
        if check_source_hash(self._json_file, fcstd_file):
            app_bin = self.get_appimage("FreeCAD")

            logging.info("Use freeCAD %s", app_bin)
            freecad_py = Path(sys.modules[self.__module__].__file__).parent / "cycax_part_freecad_bend.py"

            environment = dict(os.environ)
            environment.update(
                {
                    "CYCAX_JSON": self._json_file,
                    "CYCAX_CWD": self._base_path,
                }
            )
            result = subprocess.run(
                [app_bin, freecad_py],
                capture_output=True,
                text=True,
                env=environment,
                shell=False,
                check=False,
            )

            if result.stdout:
                logging.info("FreeCADBend: %s", result.stdout)
            if result.stderr:
                logging.error("FreeCADBend: %s", result.stderr)

        _files = [
            {"file": self._base_path / self.name / f"{self.name}.step", "description": "Folded (bent) solid."},
            {
                "file": self._base_path / self.name / f"{self.name}.FCStd",
                "description": "Live, editable FreeCAD SheetMetal document.",
            },
            {
                "file": self._base_path / self.name / f"{self.name}-unfold.step",
                "description": "Unfolded (flat) pattern.",
            },
            {
                "file": self._base_path / self.name / f"{self.name}-unfold.dxf",
                "description": "Unfolded (flat) pattern, for the manufacturer.",
            },
        ]

        return self.file_list(files=_files, engine="FreeCADBend", score=5)
