#!/usr/bin/env python3

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import Cuboid, SheetMetal
from cycax.cycad.fan import Fan

face = SheetMetal(part_no="face", x_size=50, y_size=100, z_size=2)
fan_face = Fan(width=50, depth=10, part_no="fan_face", internal=True, hole_depth=2.0, hole_diameter=3.0)
fan_face.save()
fan_face.render("OpenSCAD")

face.render("simple2D", "LEFT")


box = Assembly("box")
box.level(face.bottom, fan_face.top)
box.subtract(face.bottom, fan_face)
box.add(fan_face)
box.add(face)
box.render()
