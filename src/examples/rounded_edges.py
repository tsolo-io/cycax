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
        sheet.rounded_edge(edge_type="bevel", side1="FRONT", side2="LEFT", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="FRONT", side2="RIGHT", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="BACK", side2="LEFT", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="BACK", side2="RIGHT", radius=3)

        sheet.rounded_edge(edge_type="bevel", side1="TOP", side2="FRONT", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="BOTTOM", side2="FRONT", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="BACK", side2="TOP", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="BACK", side2="BOTTOM", radius=3)

        sheet.rounded_edge(edge_type="bevel", side1="LEFT", side2="TOP", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="LEFT", side2="BOTTOM", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="RIGHT", side2="TOP", radius=3)
        sheet.rounded_edge(edge_type="bevel", side1="RIGHT", side2="BOTTOM", radius=3)
        sheet.save(path=Path("."))
        sheet.render("preview3D")

        sheet = SheetMetal(x_size=100, y_size=200, z_size=50, part_no="sheet_taper")
        sheet.rounded_edge(edge_type="taper", side1="FRONT", side2="LEFT", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="FRONT", side2="RIGHT", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="BACK", side2="LEFT", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="BACK", side2="RIGHT", radius=3)

        sheet.rounded_edge(edge_type="taper", side1="TOP", side2="FRONT", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="BOTTOM", side2="FRONT", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="BACK", side2="TOP", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="BACK", side2="BOTTOM", radius=3)

        sheet.rounded_edge(edge_type="taper", side1="LEFT", side2="TOP", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="LEFT", side2="BOTTOM", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="RIGHT", side2="TOP", radius=3)
        sheet.rounded_edge(edge_type="taper", side1="RIGHT", side2="BOTTOM", radius=3)
        sheet.save(path=Path("."))
        sheet.render("preview3D")

    if __name__ == "__main__":
        main()
