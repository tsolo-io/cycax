# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import SheetMetal
from cycax.parts.fan import Fan
from tests.shared import hex_code_check


def fans(tmp_path: Path):
    face = SheetMetal(part_no="face", x_size=50, y_size=100, z_size=2)
    fan_face = Fan(size=50, thickness=10, part_no="fan_face", internal=True, hole_depth=2.0, hole_diameter=3.0)

    box = Assembly("box")
    face.bottom.level(fan_face.top)
    face.bottom.subtract(fan_face)
    box.add(fan_face)
    box.add(face)

    fan_face.save(tmp_path)
    face.save(tmp_path)

    face.render("freecad")
    face.render("preview3d")


def test_fans(tmp_path: Path):
    # This test checks that the fan is being produced as it should.

    fans(tmp_path)

    hex_code_check(
        tmp_path=tmp_path,
        filename="face",
        ext=".stl",
        hex_code="0279da77c3a71d93c3b70610cb39ee4f0f75aac5b673cc880a877d4ba78fbc1b",
    )
