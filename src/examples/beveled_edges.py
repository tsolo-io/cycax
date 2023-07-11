#!/usr/bin/env python3

from pathlib import Path

from cycax.cycad import Assembly, Cuboid, Print3D, SheetMetal

LEFT = "LEFT"
RIGHT = "RIGHT"
TOP = "TOP"
BOTTOM = "BOTTOM"
FRONT = "FRONT"
BACK = "BACK"


class main:
    def main():
        sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no="sheet_bevel")
        sheet.beveled_edge(edge_type="round", side1="FRONT", side2="RIGHT", radius=3)
        sheet.beveled_edge(edge_type="round", side1="FRONT", side2="LEFT", radius=3)
        sheet.beveled_edge(edge_type="round", side1="BACK", side2="LEFT", radius=3)
        sheet.beveled_edge(edge_type="round", side1="BACK", side2="RIGHT", radius=3)

        sheet.beveled_edge(edge_type="round", side1="TOP", side2="FRONT", radius=3)
        sheet.beveled_edge(edge_type="round", side1="BOTTOM", side2="FRONT", radius=3)
        sheet.beveled_edge(edge_type="round", side1="BACK", side2="TOP", radius=3)
        sheet.beveled_edge(edge_type="round", side1="BACK", side2="BOTTOM", radius=3)

        sheet.beveled_edge(edge_type="round", side1="LEFT", side2="TOP", radius=3)
        sheet.beveled_edge(edge_type="round", side1="LEFT", side2="BOTTOM", radius=3)
        sheet.beveled_edge(edge_type="round", side1="RIGHT", side2="TOP", radius=3)
        sheet.beveled_edge(edge_type="round", side1="RIGHT", side2="BOTTOM", radius=3)
        sheet.save(path=Path("."))
        sheet.render("preview3d")

        sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no="sheet_taper")
        sheet.beveled_edge(edge_type="chamfer", side1="FRONT", side2="LEFT", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="FRONT", side2="RIGHT", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="BACK", side2="LEFT", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="BACK", side2="RIGHT", length=3)

        sheet.beveled_edge(edge_type="chamfer", side1="TOP", side2="FRONT", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="BOTTOM", side2="FRONT", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="BACK", side2="TOP", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="BACK", side2="BOTTOM", length=3)

        sheet.beveled_edge(edge_type="chamfer", side1="LEFT", side2="TOP", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="LEFT", side2="BOTTOM", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="RIGHT", side2="TOP", length=3)
        sheet.beveled_edge(edge_type="chamfer", side1="RIGHT", side2="BOTTOM", length=3)
        sheet.save(path=Path("."))
        sheet.render("preview3d")

    if __name__ == "__main__":
        main()
