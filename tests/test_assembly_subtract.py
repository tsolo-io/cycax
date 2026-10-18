# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# `assembly.<side>.subtract(other_assembly)` cuts the external features of the parts that were
# added to `other_assembly` with `external_subtract=True`.
from cycax.cycad import Assembly, Print3D, SheetMetal


class Bracket(Print3D):
    def __init__(self):
        super().__init__(part_no="bracket", x_size=20, y_size=20, z_size=10)

    def definition(self):
        self.bottom.hole(pos=(10, 10), diameter=3, external_subtract=True)


def test_assembly_subtract_uses_the_external_subtract_parts():
    base = Assembly("base")
    plate = SheetMetal(part_no="plate", x_size=100, y_size=100, z_size=2)
    base.add(plate)

    stack = Assembly("stack")
    bracket = Bracket()
    stack.add(bracket, "bracket", external_subtract=True)
    stack.add(SheetMetal(part_no="spacer", x_size=5, y_size=5, z_size=5), "spacer")
    assert stack.external_feature_parts == {"bracket"}

    bracket.level(bottom=plate.top)
    features_before = len(plate.features)
    base.top.subtract(stack)
    assert len(plate.features) > features_before  # the bracket's hole was cut into the plate
