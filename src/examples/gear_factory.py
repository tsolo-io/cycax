"""A gear factory.

Note: It makes a gear like things for now.
"""

import math

from cycax.cycad import Print3D
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


class Gear(Print3D):
    """Define a gear.

    Note: It makes a gear like things for now.

    """

    def __init__(self, outer_diameter=0):
        name = f"Gear-{outer_diameter}"
        super().__init__(part_no=name, x_size=11, y_size=11, z_size=2)

    def definition(self):
        """Calculate the gear."""
        cx = self.x_size / 2
        cy = self.y_size / 2
        radius = self.x_size / 2 - 1
        self.top.hole(pos=(cx, cy), diameter=2)
        self.top.box(pos=(cx - 0.5, cy), length=1, width=1.2)
        angle = (math.pi * 2) / 12
        for n in range(1, 13):
            pos = (cx + math.cos(angle * n) * radius, cy + math.sin(angle * n) * radius)
            self.top.hole(pos=pos, diameter=1)
        self.top.hole(pos=(cx, cy), diameter=2 * radius - 1.5, depth=0.5)


if __name__ == "__main__":
    gear = Gear()
    gear.save("./build")
    cycax_server = PartEngineBuild123d()
    cycax_server.build(gear)
