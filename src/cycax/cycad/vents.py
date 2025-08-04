# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Utility functions used by the side vent cutting."""

from __future__ import annotations

from itertools import product
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cycax.cycad.cycad_side import CycadSide


class Vent:
    def __init__(
        self, x_min: float, y_min: float, x_max: float, y_max: float, separation: float | None, side: CycadSide
    ):
        self.x_min = x_min
        self.y_min = y_min
        self.x_max = x_max
        self.y_max = y_max
        self.separation = separation
        self.side = side

    def rectangle(self):
        """Cut out one big rectangle."""
        self.side.box(pos=(self.x_min, self.y_min), length=self.x_max - self.x_min, width=self.y_max - self.y_min)

    def rounded_rectangle(self, radius: float):
        """Cut out one rounded rectangle."""
        for x, y in product((self.x_min + radius, self.x_max - radius), (self.y_min + radius, self.y_max - radius)):
            self.side.hole(pos=(x, y), diameter=radius * 2)
        self.side.box(
            pos=(self.x_min, self.y_min + radius),
            length=self.x_max - self.x_min,
            width=self.y_max - self.y_min - radius * 2,
        )
        self.side.box(
            pos=(self.x_min + radius, self.y_min),
            length=self.x_max - self.x_min - radius * 2,
            width=self.y_max - self.y_min,
        )

    def circle(self):
        """Cut out the biggest possible circle."""
        diameter = min(self.x_max - self.x_min, self.y_max - self.y_min)
        self.side.hole(pos=((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2), diameter=diameter)

    def circles_grid(self, diameter: float):
        """Cut out a grid of circles."""
        radius = diameter / 2
        if not self.separation:
            separation = radius
        else:
            separation = self.separation
        length = self.x_max - self.x_min
        width = self.y_max - self.y_min
        x_count = int((length + separation) / (diameter + separation))
        y_count = int((width + separation) / (diameter + separation))
        start_x = radius + self.x_min + (length - diameter * x_count - separation * (x_count - 1)) / 2
        start_y = radius + self.y_min + (width - diameter * y_count - separation * (y_count - 1)) / 2
        for x, y in product(range(x_count), range(y_count)):
            self.side.hole(
                pos=(start_x + x * (diameter + separation), start_y + y * (diameter + separation)), diameter=diameter
            )
