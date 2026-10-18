# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Small DSL features (task cycax/36)."""

import math

import pytest

import cycax
from cycax import testing
from cycax.app.tools import FreeCADLocalTool, OpenSCADTool
from cycax.cycad import Assembly, Print3D
from cycax.cycad.colour import to_rgb


def test_colours():
    assert to_rgb("#ff8000") == [1.0, 0.502, 0.0]
    assert to_rgb("#f80") == [1.0, 0.533, 0.0]
    assert to_rgb((255, 128, 0)) == pytest.approx([1.0, 0.502, 0.0], abs=1e-3)
    assert to_rgb("silver") == [0.753, 0.753, 0.753]


def test_assembly_definition_is_called():
    class Pair(Assembly):
        def definition(self):
            self.add(Print3D(part_no="a", x_size=1, y_size=1, z_size=1))

    assert len(Pair("pair").parts) == 1


def test_iso_nuts():
    part = Print3D(part_no="p", x_size=30, y_size=30, z_size=10)
    for size in ("M2", "M2.5", "M4", "M5", "M8", "M10", "M12"):
        part.top.nut(pos=(15, 15), nut_type=f"{size}ISO")
    assert len(part.export()["features"]) == 8


def test_patterns():
    part = Print3D(part_no="p", x_size=60, y_size=40, z_size=5)
    part.top.pattern_linear("hole", start=(10, 10), count=5, step=(10, 0), diameter=3)
    part.top.pattern_circular("hole", centre=(30, 25), radius=10, count=6, diameter=2)
    holes = [f for f in part.export()["features"] if f["name"] == "hole"]
    assert len(holes) == 11
    assert [h["x"] for h in holes[:5]] == [10, 20, 30, 40, 50]
    assert holes[5]["x"] == pytest.approx(40)  # angle 0: centre + radius


def countersunk_plate():
    part = Print3D(part_no="cs_plate", x_size=40, y_size=20, z_size=5)
    part.top.hole(pos=(20, 10), diameter=3.4, countersink=6.4)
    part.front.rectangle(pos=(5, 1), width=10, height=2, depth=4)
    part.top.polygon(pos=(8, 10), sides=6, diameter=4, depth=2)
    return part


def test_countersink_volume(tmp_path):
    result = cycax.build(countersunk_plate(), outputs=["step"], backend="local", project_dir=tmp_path)
    target = next(iter(result.targets.values()))
    assert target.error is None, target.error
    volume = testing.measure(target.files["step"]).volume
    h = (6.4 - 3.4) / 2  # 90 degrees: depth = (D - d) / 2
    cone = math.pi * h / 3 * (3.2**2 + 3.2 * 1.7 + 1.7**2)
    hole = math.pi * 1.7**2 * 5
    hexagon = 3 * math.sqrt(3) / 2 * 2**2 * 2
    expected = 40 * 20 * 5 - hole - (cone - math.pi * 1.7**2 * h) - 10 * 2 * 4 - hexagon
    assert volume == pytest.approx(expected, rel=1e-6)


def test_countersink_must_be_wider():
    part = Print3D(part_no="p", x_size=10, y_size=10, z_size=5)
    with pytest.raises(ValueError, match="wider"):
        part.top.hole(pos=(5, 5), diameter=4, countersink=3)


@pytest.mark.skipif(not (FreeCADLocalTool().available() and OpenSCADTool().available()), reason="FreeCAD/OpenSCAD")
@pytest.mark.slow
def test_countersink_in_all_engines(tmp_path):
    part = Print3D(part_no="cs_only", x_size=40, y_size=20, z_size=5)
    part.top.hole(pos=(20, 10), diameter=3.4, countersink=6.4)
    result = testing.cross_engine(part, ["build123d", "freecad", "openscad"], tmp_path)
    assert result.ok, result.report()
