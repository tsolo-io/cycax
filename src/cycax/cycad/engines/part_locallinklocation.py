# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from pathlib import Path

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.engines.utils import check_source_hash


class PartEngineLLL(PartEngine):
    """
    Use symlinks at a specific location to run Jobs on FreeCAD.
    """

    def check_part_init(self):
        """Early hook for part classes to do custom checks."""
        self.config["freecad_jobs_location"]

    def create(self, part):
        part.save()

    def build(self, part) -> list:
        """Create the output files for the part."""

        timestamp = int(time.time())
        symlink_part_path = self.config["freecad_jobs_location"] / f"{timestamp}.{self.name}"

        Path(symlink_part_path).symlink_to(part.path)

        for _ in range(29):
            if symlink_part_path.exists():
                time.sleep(1)
            else:
                break

        _files = []

        return self.file_list(files=_files, engine="OpenSCAD", score=3)
