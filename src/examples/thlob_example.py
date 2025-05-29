#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid, Print3D, SheetMetal


class Thing(Cuboid):
    def __init__(self):
        super().__init__(part_no="Thing", x_size=10, y_size=10, z_size=26)
        self.calculate()

    def calculate(self):
        for x in [4, 6]:
            for y in [4, 6]:
                self.top.hole(pos=[x, y], diameter=2, depth=12)
                self.bottom.hole(pos=[x, y], diameter=3, depth=12)
                self.bottom.hole(pos=[x, y], diameter=3.1, depth=12, inner=False)
                self.top.hole(pos=[x, y], diameter=3.1, depth=12, inner=False)

        self.front.box(
            pos=[self.x_size / 3, 5],
            width=(self.x_size) / 3,
            depth=self.y_size / 3 + 2,
            length=self.z_size - 10,
            sink=-1,
        )
        self.left.box(
            pos=[self.x_size / 3, 5],
            width=(self.x_size) / 3,
            depth=self.y_size / 3 + 2,
            length=self.z_size - 10,
            sink=-1,
        )


class Blob(Print3D):  # ExternalPart):
    def __init__(self):
        super().__init__(part_no="Blob", x_size=10, y_size=10, z_size=10)
        self.calculate()

    def calculate(self):
        for x in [4, 6]:
            for y in [4, 6]:
                self.bottom.hole(pos=[x, y], diameter=2)


def main():
    assembly = Assembly(part_no="Thlob")
    base_board = SheetMetal(part_no="BaseBoard", x_size=1100, y_size=100, z_size=15)

    for thing_no in range(1, 11):
        thing = Thing()
        thing.move(x=thing_no * 100)
        assembly.level(thing.bottom, base_board.top)
        assembly.level(thing.back, base_board.back)
        assembly.subtract(base_board.top, thing)
        assembly.add(thing)

        blob = Blob()
        blob.calculate()
        assembly.level(blob.bottom, thing.top)
        assembly.level(blob.back, thing.back)
        assembly.level(blob.left, thing.left)
        assembly.add(blob)

    assembly.add(base_board)
    assembly.render()


if __name__ == "__main__":
    main()
