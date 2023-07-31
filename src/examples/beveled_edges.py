#!/usr/bin/env python3

from pathlib import Path

from cycac.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP

from cycax.cycad import SheetMetal


def main():
    sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no="sheet_bevel")
    sheet.beveled_edge(edge_type="round", side1=FRONT, side2=RIGHT, size=3)
    sheet.beveled_edge(edge_type="round", side1=FRONT, side2=LEFT, size=3)
    sheet.beveled_edge(edge_type="round", side1=BACK, side2=LEFT, size=3)
    sheet.beveled_edge(edge_type="round", side1=BACK, side2=RIGHT, size=3)

    sheet.beveled_edge(edge_type="round", side1=TOP, side2=FRONT, size=3)
    sheet.beveled_edge(edge_type="round", side1=BOTTOM, side2=FRONT, size=3)
    sheet.beveled_edge(edge_type="round", side1=BACK, side2=TOP, size=3)
    sheet.beveled_edge(edge_type="round", side1=BACK, side2=BOTTOM, size=3)

    sheet.beveled_edge(edge_type="round", side1=LEFT, side2=TOP, size=3)
    sheet.beveled_edge(edge_type="round", side1=LEFT, side2=BOTTOM, size=3)
    sheet.beveled_edge(edge_type="round", side1=RIGHT, side2=TOP, size=3)
    sheet.beveled_edge(edge_type="round", side1=RIGHT, side2=BOTTOM, size=3)
    sheet.save(path=Path("."))
    sheet.render("preview3d")

    sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no="sheet_taper")
    sheet.beveled_edge(edge_type="chamfer", side1=FRONT, side2=LEFT, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=FRONT, side2=RIGHT, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=BACK, side2=LEFT, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=BACK, side2=RIGHT, size=3)

    sheet.beveled_edge(edge_type="chamfer", side1=TOP, side2=FRONT, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=BOTTOM, side2=FRONT, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=BACK, side2=TOP, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=BACK, side2=BOTTOM, size=3)

    sheet.beveled_edge(edge_type="chamfer", side1=LEFT, side2=TOP, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=LEFT, side2=BOTTOM, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=RIGHT, side2=TOP, size=3)
    sheet.beveled_edge(edge_type="chamfer", side1=RIGHT, side2=BOTTOM, size=3)
    sheet.save(path=Path("."))
    sheet.render("preview3d")


if __name__ == "__main__":
    main()
