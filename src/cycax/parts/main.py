# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from cycax.cycad import Assembly, SheetMetal
from cycax.parts.fan import Fan80x80x25


def build_fan80(*, internal: bool):
    name = "Fan80x80x25-{}".format("internal" if internal else "external")
    assembly = Assembly(name)
    plate = SheetMetal(f"{name}-sheet", x_size=100, y_size=100, z_size=1)
    fan = Fan80x80x25(internal=internal)

    assembly.add(plate)
    assembly.add(fan)
    assembly.level(fan.top, plate.bottom)
    assembly.level(fan.left, plate.left)
    assembly.level(fan.front, plate.front)
    fan.move(x=10, y=10)
    assembly.subtract(plate.bottom, fan)
    for part in (fan, plate):
        part.save(path=Path("./reports"))
        part.render(engine="simple2d")
        # part.render(engine="openscad")
        # part.render(engine="freecad")


if __name__ == "__main__":
    for internal in (True, False):
        build_fan80(internal=internal)
