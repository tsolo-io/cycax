# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Demonstration of vents."""

from cycax.cycad import SheetMetal
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


class VentsExample(SheetMetal):
    """Define a part with vents."""

    def __init__(self):
        super().__init__(part_no="vents", x_size=200, y_size=100, z_size=2)

    def definition(self):
        """Calculate the gear."""
        self.top.vent(x_min=0, x_max=100, y_min=0, y_max=50, border=5).rounded_rectangle(radius=10)
        self.top.vent(x_min=0, x_max=100, y_min=50, y_max=100, border=5).rectangle()
        self.top.vent(x_min=100, x_max=200, y_min=0, y_max=50, border=5).circle()
        self.top.vent(x_min=100, x_max=200, y_min=50, y_max=100, border=5).circles_grid(diameter=6)


if __name__ == "__main__":
    ventexample = VentsExample()
    ventexample.save("./build")
    cycax_server = PartEngineBuild123d()
    cycax_server.build(ventexample)
