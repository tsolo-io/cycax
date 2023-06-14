#!/usr/bin/env python3
from pathlib import Path

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid
from cycax.cycad.external_part import ExternalPart
from cycax.cycad.sheet_metal import SheetMetal


class Thing(Cuboid):
    part_no = "thing7653"
    x_size = 10
    y_size = 10
    z_size = 26

    def calculate(self):
        for x in [4, 6]:
            for y in [4, 6]:
                self.make_hole(x, y, "TOP", diameter=2, depth=12)
                self.make_hole(x, y, "BOTTOM", diameter=3, depth=12)
                self.make_hole(x, y, "BOTTOM", diameter=3.1, depth=12, inner=False)
                self.make_hole(x, y, "TOP", diameter=3.1, depth=12, inner=False)


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
    assembly.add(base_board)

    for thing_no in range(1, 11):
        thing = Thing("Thing", 10, 10, 26)
        thing.calculate()
        thing.move(x=thing_no * 10)
        assembly.level(thing, "BOTTOM", base_board, "TOP")
        assembly.level(thing, "BACK", base_board, "BACK")
        assembly.add(thing)

        blob = Blob("Blob", 10, 10, 10)
        blob.calculate()
        assembly.level(blob, "BOTTOM", thing, "TOP")
        assembly.level(blob, "BACK", thing, "BACK")
        assembly.level(blob, "LEFT", thing, "LEFT")
        assembly.add(blob)

    assembly.render()


if __name__ == "__main__":
    main()
