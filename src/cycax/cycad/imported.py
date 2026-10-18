# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Parts from imported STEP/STL files, e.g. vendor models (task cycax/35).

    from cycax.cycad import ImportedPart

    psu = ImportedPart(part_no="meanwell_psu", file="vendor/meanwell.step")
    psu.top.hole(pos=(20, 10), diameter=3)      # features: STEP imports only
    assembly.add(psu)

Only files in the project: CyCAx never downloads. The model is moved so that the minimum corner
of its bounding box is at 0,0,0 (`offset` records the move). The spec has the file name, the
format, the file's SHA-256 (a changed file gives a new part hash), the size and the offset.
Builds copy the file to the engine (local) or put it in the cache as
`<hash>/<name>-import.<format>` (server).
"""

import hashlib
from pathlib import Path

from cycax.cycad.cycad_part import CycadPart
from cycax.cycad.location import BOTTOM

FORMATS = {".step": "step", ".stp": "step", ".stl": "stl"}


def model_bounds(path: Path, fmt: str) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if fmt == "stl":
        from cycax.testing import read_stl  # noqa: PLC0415 - numpy only

        points = read_stl(path).reshape(-1, 3)
        return tuple(float(v) for v in points.min(axis=0)), tuple(float(v) for v in points.max(axis=0))
    import build123d  # noqa: PLC0415 - only for STEP imports

    box = build123d.import_step(path).bounding_box()
    return (box.min.X, box.min.Y, box.min.Z), (box.max.X, box.max.Y, box.max.Z)


class ImportedPart(CycadPart):
    """A part made from a STEP or STL file of the project.

    Args:
        part_no: The part number.
        file: The STEP (.step/.stp) or STL file, relative to the current folder or absolute.
    """

    def __init__(self, part_no: str, file: str | Path, *, assembly=None, colour=None, material=None, manufacture=None):
        path = Path(file).expanduser().resolve()
        if not path.is_file():
            msg = f"No file {path} (CyCAx only imports files of the project; it does not download)."
            raise FileNotFoundError(msg)
        fmt = FORMATS.get(path.suffix.lower())
        if fmt is None:
            msg = f"Cannot import {path.name}: use a STEP (.step, .stp) or STL (.stl) file."
            raise ValueError(msg)
        lo, hi = model_bounds(path, fmt)
        self.source_path = path
        self.import_format = fmt
        self.sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        self.offset = tuple(round(-v, 9) + 0.0 for v in lo)
        size = tuple(b - a for a, b in zip(lo, hi, strict=True))
        super().__init__(
            x=0.0,
            y=0.0,
            z=0.0,
            side=BOTTOM,
            part_no=part_no,
            x_size=size[0],
            y_size=size[1],
            z_size=size[2],
            polygon="import",
            assembly=assembly,
            colour=colour,
            material=material,
            manufacture=manufacture,
            default_colour="gray",
        )

    @property
    def source_files(self) -> dict[str, Path]:
        """File name in the spec -> the file on this computer (for the builder)."""
        return {self.source_path.name: self.source_path}

    def base_feature(self) -> dict:
        if self.import_format == "stl" and self.features:
            msg = (
                f"{self.part_no}: holes and cuts work on STEP imports only, not on STL (a mesh). "
                "Use the STEP file of the model."
            )
            raise ValueError(msg)
        return {
            "name": "import",
            "type": "import",
            "action": "add",
            "side": BOTTOM,
            "file": self.source_path.name,
            "format": self.import_format,
            "sha256": self.sha256,
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "x_size": float(self.x_size),
            "y_size": float(self.y_size),
            "z_size": float(self.z_size),
            "offset": [float(v) for v in self.offset],
        }


def import_object_name(spec: dict) -> str | None:
    """The cache object name of an imported part's file: `<name>-import.<format>`."""
    base = spec.get("features", [{}])[0]
    if base.get("type") != "import":
        return None
    return f"{spec['name']}-import.{base['format']}"
