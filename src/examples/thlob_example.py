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
        for x in (4.0, 6.0):
            for y in (4.0, 6.0):
                self.top.hole(pos=(x, y), diameter=2, depth=12)
                self.bottom.hole(pos=(x, y), diameter=3, depth=12)
                self.bottom.hole(pos=(x, y), diameter=3.1, depth=12)
                self.top.hole(pos=(x, y), diameter=3.1, depth=12)

        self.front.box(
            pos=(self.x_size / 3, 5),
            width=self.x_size / 3,
            depth=self.y_size / 3 + 2,
            length=self.z_size - 10,
            sink=-1,
        )
        self.left.box(
            pos=(self.x_size / 3, 5),
            width=self.x_size / 3,
            depth=self.y_size / 3 + 2,
            length=self.z_size - 10,
            sink=-1,
        )


class Blob(Print3D):
    def __init__(self):
        super().__init__(part_no="Blob", x_size=10, y_size=10, z_size=10)
        self.calculate()

    def calculate(self):
        for x in [4, 6]:
            for y in [4, 6]:
                self.bottom.hole(pos=(x, y), diameter=2)


def main():
    assembly = Assembly("Thlob")
    base_board = SheetMetal(part_no="BaseBoard", x_size=1100, y_size=100, z_size=15)

    for thing_no in range(1, 11):
        thing = Thing()
        thing.move(x=thing_no * 100)
        thing.bottom.level(base_board.top)
        thing.back.level(base_board.back)
        base_board.top.subtract(thing)
        assembly.add(thing)

        blob = Blob()
        blob.calculate()
        blob.bottom.level(thing.top)
        blob.back.level(thing.back)
        blob.left.level(thing.left)
        assembly.add(blob)

    assembly.add(base_board)
    assembly.save("./build/thlob")
    assembly.render()


if __name__ == "__main__":
    main()
