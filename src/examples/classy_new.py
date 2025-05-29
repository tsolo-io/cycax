#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import SheetMetal

moving = SheetMetal(part_no="face", x_size=50, y_size=100, z_size=2)

box = Assembly("box")
box.rotateFreezeLeft(moving)
box.rotateFreezeLeft(moving)
box.rotateFreezeFront(moving)
box.rotateFreezeTop(moving)
box.rotateFreezeLeft(moving)
box.rotateFreezeLeft(moving)
box.rotateFreezeFront(moving)
box.rotateFreezeTop(moving)
box.add(moving)
box.render()
