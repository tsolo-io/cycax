# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import subprocess
from pathlib import Path

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.utils import check_source_hash

# Feature types that only the FreeCAD bend engine (SheetMetal workbench) understands. A part
# with any of these must be built by `run_freecad_bend`, not the generic FreeCAD engine, which
# would ignore them silently.
SHEET_METAL_FEATURE_TYPES = frozenset(
    {"bend", "flange_hole_cut", "flat_rectangle_cut", "flat_polygon_cut", "flange_corner_round"}
)


def is_sheet_metal_bend(definition: dict) -> bool:
    """True when a part spec needs the FreeCAD bend engine."""
    return any(feature.get("type") in SHEET_METAL_FEATURE_TYPES for feature in definition.get("features", []))


def run_freecad_bend(app_bin: Path, json_file: Path, base_path: Path) -> subprocess.CompletedProcess:
    """Build one sheet-metal part with `cycax_part_freecad_bend.py` inside FreeCAD.

    Args:
        app_bin: The FreeCAD binary or AppImage.
        json_file: The part JSON.
        base_path: The folder that holds the part folder (outputs go to `<base_path>/<name>/`).
    """
    freecad_py = Path(__file__).resolve().parent / "cycax_part_freecad_bend.py"
    environment = dict(os.environ)
    environment.update({"CYCAX_JSON": str(json_file), "CYCAX_CWD": str(base_path)})
    result = subprocess.run(
        [str(app_bin), str(freecad_py)],
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
    return result


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
            run_freecad_bend(app_bin, self._json_file, self._base_path)

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
