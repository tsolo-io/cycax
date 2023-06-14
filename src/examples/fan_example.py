#!/usr/bin/env python3

from cycax.cycad.assembly import Assembly
from cycax.cycad.engine_openscad import EngineOpenSCAD
from cycax.cycad.fan import Fan
from cycax.cycad.figure import Figure
from cycax.cycad.sheet_metal import SheetMetal

face = SheetMetal(part_no="face", x_size=50, y_size=100, z_size=2)
fan_face = Fan(width=50, depth=10, part_no="fan_face", internal=True, hole_depth=2.0, hole_diameter=3.0)
eng = EngineOpenSCAD()
eng.add(fan_face)
eng.decode("fan_face")

draw = Figure("fan_face", "TOP")
draw.save_as_figure()

box = Assembly("box")
box.level(face, "BOTTOM", fan_face, "TOP")
box.subtract(face, "BOTTOM", fan_face)
box.add(fan_face)
box.add(face)
box.render()
