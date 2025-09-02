"""Create a Pipe Flange."""

import math
from pathlib import Path

from cycax.cycad import Cylinder
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


class PipeFlange(Cylinder):
    """Pipe Flange is a cylinder with a flange."""

    def __init__(self, *, thickness: float = 2.0, diameter: float = 20, inner_diameter: float = 10, holes: int = 8):
        self.thickness = thickness
        self.diameter = diameter
        self.inner_diameter = inner_diameter
        self.holes = holes
        name = f"Pipe-Flange-{diameter}-{inner_diameter}"
        super().__init__(part_no=name, diameter=diameter, height=thickness)

    def definition(self):
        """Definition of the Pipe Flange."""
        # Cut out part of the box to create a L-shaped rack strip
        angle = (math.pi * 2) / self.holes
        radius = self.radius - (self.radius - self.inner_diameter / 2 - self.thickness) / 2
        for n in range(1, self.holes + 1):
            pos = (self.x_center + math.cos(angle * n) * radius, self.y_center + math.sin(angle * n) * radius)
            self.bottom.hole(pos=pos, diameter=1)
        self.top.cylinder(pos=(self.x_center, self.y_center), diameter=self.inner_diameter + self.thickness, height=40)
        self.top.cylinder(pos=(self.x_center, self.y_center), diameter=self.diameter, height=self.thickness)
        # radius = self.radius - (self.radius - self.inner_diameter / 2 - self.thickness) / 2
        for n in range(1, self.holes + 1):
            pos = (self.x_center + math.cos(angle * n) * radius, self.y_center + math.sin(angle * n) * radius)
            self.top.hole(pos=pos, diameter=1, depth=2 * self.thickness)
        self.bottom.hole(pos=(self.x_center, self.y_center), diameter=self.inner_diameter)

        self.front.cylinder(pos=(self.x_center, 15), diameter=8, height=20, sink=self.diameter / 2)
        self.front.cylinder(pos=(self.x_center, 15), diameter=12, height=self.thickness)
        self.front.hole(pos=(self.x_center, 15), diameter=8 - self.thickness * 2, depth=20 + self.thickness * 2)
        radius = 5
        for n in range(1, self.holes + 1):
            pos = (self.x_center + math.cos(angle * n) * radius, 15 + math.sin(angle * n) * radius)
            self.front.hole(pos=pos, diameter=1, depth=2 * self.thickness)


if __name__ == "__main__":
    flange = PipeFlange(diameter=20, inner_diameter=10, thickness=2)
    flange.save(Path(f"./build/{flange.part_no}"))
    flange.build(PartEngineBuild123d())
