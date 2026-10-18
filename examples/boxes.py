# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Pockets and bosses.

`side.box(pos, length, width, depth)` cuts a rectangular pocket into a side; `side.box_add(...)`
adds a rectangular block onto a side. `pos` is a corner of the rectangle as seen from that side.
All sizes are in mm.
"""

from cycax import cycax_part
from cycax.cycad import Print3D


@cycax_part(doc_view="top")
def pocket() -> Print3D:
    """A pocket 20 x 10 mm and 2 mm deep."""
    plate = Print3D(part_no="pocket", x_size=40, y_size=30, z_size=5)
    plate.top.box(pos=(10, 10), length=20, width=10, depth=2)
    return plate


@cycax_part(doc_view="front")
def boss() -> Print3D:
    """A block 10 x 10 mm and 8 mm high on top of the plate."""
    plate = Print3D(part_no="boss", x_size=40, y_size=30, z_size=5)
    plate.top.box_add(pos=(15, 10), length=10, width=10, depth=8)
    return plate
