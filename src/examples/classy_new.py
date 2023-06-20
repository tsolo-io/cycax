#!/usr/bin/env python3

from cycax.cycad import Cuboid

classy = Cuboid(part_no="classy classy", x_size=10, y_size=10, z_size=10)

classy.left.hole(pos=(5, 5), diameter=2)

classy.right.box(pos=(5, 5), width=4, length=2)

classy.top.nut(pos=(2, 4), nut_type=3, depth=2, sink=1)

classy.bottom.slot(pos=(6, 6), width=2, length=2)
