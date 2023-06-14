#!/usr/bin/env python3
from pathlib import Path

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid
from cycax.cycad.external_part import ExternalPart
from cycax.cycad.sheet_metal import SheetMetal


class Thing(Cuboid):
    def __init__(self):
        super().__init__(part_no="Thing", x_size=10, y_size=10, z_size=26, colour="red")
        self.calculate()

    def calculate(self):
        for x in [4, 6]:
            for y in [4, 6]:
                self.make_hole(x, y, "TOP", diameter=2, depth=12)
                self.make_hole(x, y, "BOTTOM", diameter=3, depth=12)
                self.make_hole(x, y, "BOTTOM", diameter=3.1, depth=12, inner=False)
                self.make_hole(x, y, "TOP", diameter=3.1, depth=12, inner=False)

        self.make_rectangle(
            side="FRONT",
            x=self.x_size / 3,
            y=5,
            x_size=(self.x_size) / 3,
            y_size=self.y_size / 3 + 2,
            z_size=self.z_size - 10,
            sink=-1,
        )
        self.make_rectangle(
            side="LEFT",
            x=self.x_size / 3,
            y=5,
            y_size=(self.x_size) / 3,
            x_size=self.y_size / 3 + 2,
            z_size=self.z_size - 10,
            sink=-1,
        )


class Blob(Cuboid):  # ExternalPart):
    part_no = "Blob-XD-F-0"
    model_file = Path("~/Downloads/stolen/STL/Blob.stl")
    x_size = 10
    y_size = 10
    z_size = 10

    def calculate(self):
        for x in [4, 6]:
            for y in [4, 6]:
                self.make_hole(x, y, "BOTTOM", diameter=2, depth=12)


def main():
    assembly = Assembly(part_number="Thlob")  # TODO: part_no or part_number
    base_board = SheetMetal(part_no="BaseBoard", x_size=1100, y_size=100, z_size=15)

    for thing_no in range(1, 11):
        thing = Thing()
        thing.move(x=thing_no * 100)
        assembly.level(thing, "BOTTOM", base_board, "TOP")
        assembly.level(thing, "BACK", base_board, "BACK")
        assembly.subtract(base_board, "TOP", thing)
        assembly.add(thing)

        blob = Blob("Blob", 10, 10, 10)
        blob.calculate()
        assembly.level(blob, "BOTTOM", thing, "TOP")
        assembly.level(blob, "BACK", thing, "BACK")
        assembly.level(blob, "LEFT", thing, "LEFT")
        assembly.add(blob)

    assembly.add(base_board)
    assembly.render()


if __name__ == "__main__":
    main()
