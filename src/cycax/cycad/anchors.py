# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Anchors: exact reference frames on a part that turn with it (task cycax/37).

Bounding boxes are not good enough to join rotated parts. An anchor is a point, an outward
normal and an x direction in the part's own coordinates; `part.anchor(name)` gives it in world
coordinates, through the part's placement (`turn()`, `rotate()`, `move()`, `level()`).

- Every part has the six faces of its base shape: `"top"`, `"bottom"`, `"left"`, `"right"`,
  `"front"`, `"back"` (the centre of the face, the outward normal).
- A hole with `name=` is an anchor: its entry point on the surface, its axis pointing out.
- Custom anchors: `part.anchor("mount", pos=(x, y, z), normal=(0, 0, 1), x_dir=(1, 0, 0))`.

Anchors are in the spec `meta` (they do not change the shape, so not the hash). Mates (cycax/38)
use them.
"""

from dataclasses import dataclass

from cycax.cycad import placement

FACE_NORMALS = {
    "top": (0.0, 0.0, 1.0),
    "bottom": (0.0, 0.0, -1.0),
    "left": (-1.0, 0.0, 0.0),
    "right": (1.0, 0.0, 0.0),
    "front": (0.0, -1.0, 0.0),
    "back": (0.0, 1.0, 0.0),
}
FACE_X = {
    "top": (1.0, 0.0, 0.0),
    "bottom": (1.0, 0.0, 0.0),
    "left": (0.0, -1.0, 0.0),
    "right": (0.0, 1.0, 0.0),
    "front": (1.0, 0.0, 0.0),
    "back": (-1.0, 0.0, 0.0),
}
# Side names of the DSL (TOP, LEFT, ...) -> anchor names
SIDE_ANCHOR = {"TOP": "top", "BOTTOM": "bottom", "LEFT": "left", "RIGHT": "right", "FRONT": "front", "BACK": "back"}


def _clean(values) -> tuple[float, float, float]:
    return tuple(round(float(v), 9) + 0.0 for v in values)


@dataclass(frozen=True)
class Anchor:
    name: str
    origin: tuple[float, float, float]
    normal: tuple[float, float, float]
    x_dir: tuple[float, float, float]

    def transformed(self, matrix: placement.Matrix) -> "Anchor":
        """This anchor moved by a 4 x 4 placement (points move, directions only turn)."""
        rotation_only = [row[:3] + [0.0] for row in matrix[:3]] + [[0.0, 0.0, 0.0, 1.0]]
        return Anchor(
            self.name,
            _clean(placement.apply(matrix, self.origin)),
            _clean(placement.apply(rotation_only, self.normal)),
            _clean(placement.apply(rotation_only, self.x_dir)),
        )

    def to_meta(self) -> dict:
        return {"origin": list(self.origin), "normal": list(self.normal), "x_dir": list(self.x_dir)}


def face_anchors(size: tuple[float, float, float]) -> dict[str, Anchor]:
    """The six faces of a base box 0..size (part coordinates)."""
    x, y, z = size
    centres = {
        "top": (x / 2, y / 2, z),
        "bottom": (x / 2, y / 2, 0.0),
        "left": (0.0, y / 2, z / 2),
        "right": (x, y / 2, z / 2),
        "front": (x / 2, 0.0, z / 2),
        "back": (x / 2, y, z / 2),
    }
    return {name: Anchor(name, _clean(centres[name]), FACE_NORMALS[name], FACE_X[name]) for name in centres}
