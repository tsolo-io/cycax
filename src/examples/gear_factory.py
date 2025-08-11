# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""A gear factory.

Note: It makes a gear like things for now.
"""

import math

from cycax.cycad import Cylinder
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


class Gear(Cylinder):
    """Define a gear.

    Note: It makes a gear like things for now.

    """

    def __init__(self, diameter: float, teath: int = 12):
        name = f"Gear-{diameter}-{teath}"
        self.teath = teath
        if diameter < 10:  # noqa PLR2004 Magic value used
            msg = "Diameter must be greater than 10"
            raise ValueError(msg)
        if teath < 6:  # noqa PLR2004 Magic value used
            msg = "Teeth must be greater than 6"
            raise ValueError(msg)
        super().__init__(part_no=name, diameter=diameter, height=3)

    def definition(self):
        """Calculate the gear."""
        self.bottom.hole(pos=(self.x_center, self.y_center), diameter=2)
        self.top.box(pos=(self.x_center - 0.5, self.y_center), length=1, width=1.2)
        teath_diameter = math.pi * self.diameter / self.teath
        angle = (math.pi * 2) / self.teath
        radius = self.diameter / 2
        for n in range(1, self.teath + 1):
            pos = (self.x_center + math.cos(angle * n) * radius, self.y_center + math.sin(angle * n) * radius)
            self.top.hole(pos=pos, diameter=teath_diameter)
        self.top.hole(pos=(self.x_center, self.y_center), diameter=2 * radius - teath_diameter - 2, depth=0.5)


if __name__ == "__main__":
    gear = Gear(diameter=10, teath=6)
    gear.save("./build")
    cycax_server = PartEngineBuild123d()
    cycax_server.build(gear)
