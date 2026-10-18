# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Holes.

`side.hole(pos, diameter)` drills a round hole into a side of a part. `pos` is the centre of
the hole as seen from that side. All sizes are in mm.
"""

from cycax import cycax_part
from cycax.cycad import Print3D


@cycax_part(doc_view="top")
def through_hole() -> Print3D:
    """A 4.2 mm hole through the plate: the default depth is the full part."""
    plate = Print3D(part_no="through_hole", x_size=30, y_size=20, z_size=5)
    plate.top.hole(pos=(15, 10), diameter=4.2)
    return plate


@cycax_part(doc_view="top")
def blind_hole() -> Print3D:
    """A hole 3 mm deep: give a `depth`."""
    plate = Print3D(part_no="blind_hole", x_size=30, y_size=20, z_size=5)
    plate.top.hole(pos=(15, 10), diameter=6, depth=3)
    return plate


@cycax_part(doc_view="top")
def hole_pattern() -> Print3D:
    """Use a Python loop for a row of holes, 10 mm apart."""
    plate = Print3D(part_no="hole_pattern", x_size=60, y_size=20, z_size=5)
    for x in range(10, 60, 10):
        plate.top.hole(pos=(x, 10), diameter=3)
    return plate


@cycax_part(doc_view="right")
def side_hole() -> Print3D:
    """Holes can be drilled into any side. This one goes into the right side."""
    block = Print3D(part_no="side_hole", x_size=30, y_size=20, z_size=20)
    block.right.hole(pos=(10, 10), diameter=5, depth=15)
    return block
