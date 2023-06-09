#!/usr/bin/env python3

from cycax.cycad.engine_openscad import EngineOpenSCAD
from cycax.cycad.fan import Fan
from cycax.cycad.figure import Figure
from cycax.cycad.sheet_metal import SheetMetal

face = SheetMetal(part_no="face", x_size=50, y_size=100, z_size=2)
f = Fan(width=50, surface=face, x=25, y=50, internal=True, depth=2.0, hole_diameter=3.0)
eng = EngineOpenSCAD()
eng.add(face)
eng.decode("face")

draw = Figure("face", "TOP")
draw.save_as_figure()
