# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Utility functions used by the side vent cutting."""

from cycax.cycad.cycad_side import CycadSide


def hole_grid(
    side: CycadSide,
    pos: tuple[float, float] = (0.0, 0.0),
    length: float = 1.0,
    width: float = 1.0,
    spacing: float = 1.0,
    border: float = 0.0,
    min_diameter: float = 1.0,
    max_diameter: float = 10.0,
):
    """Create a grid of holes.

    Args:
        side: The side of the grid.
        pos: The position of the grid.
        length: The length of the grid.
        width: The width of the grid.
        spacing: The minimum spacing between holes.
        border: The minimum border around the grid.
        min_diameter: The minimum diameter of the holes.
        max_diameter: The maximum diameter of the holes.

    Returns:
        list[Circle]: A list of circles representing the holes.
    """
    if border <= 0.0:
        x, y = pos
        l = length
        w = width
    else:
        x, y = pos[0] + border, pos[1] + border
        l = length - border
        w = width - border
