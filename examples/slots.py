# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Slots.

A slot is a long hole with round ends. `side.slot(pos, length, width)` cuts a slot into a side of
a part: `pos` is the centre of the first round end, as seen from that side; the slot runs
`length` mm from there. All sizes are in mm.
"""

from cycax import cycax_part
from cycax.cycad import Print3D


@cycax_part(doc_view="top")
def horizontal_slot() -> Print3D:
    """A slot that runs left to right (the default), through the plate."""
    plate = Print3D(part_no="horizontal_slot", x_size=60, y_size=30, z_size=4)
    plate.top.slot(pos=(10, 15), length=40, width=6)
    return plate


@cycax_part(doc_view="top")
def vertical_slot() -> Print3D:
    """A slot that runs front to back: `horizontal=False`."""
    plate = Print3D(part_no="vertical_slot", x_size=60, y_size=30, z_size=4)
    plate.top.slot(pos=(30, 5), length=20, width=6, horizontal=False)
    return plate


@cycax_part(doc_view="top")
def blind_slot() -> Print3D:
    """A slot that is 2 mm deep: give a `depth`. Without a depth the slot goes through."""
    plate = Print3D(part_no="blind_slot", x_size=60, y_size=30, z_size=4)
    plate.top.slot(pos=(10, 15), length=40, width=8, depth=2)
    return plate


@cycax_part(doc_view="front")
def slot_in_the_front() -> Print3D:
    """Slots can be cut into any side. This one is in the front of a block."""
    block = Print3D(part_no="slot_in_the_front", x_size=60, y_size=20, z_size=30)
    block.front.slot(pos=(15, 15), length=30, width=5, depth=10)
    return block
