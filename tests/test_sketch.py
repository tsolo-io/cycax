# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""2D sketches and DXF import (task cycax/34)."""

import math

import ezdxf
import pytest

import cycax
from cycax import testing
from cycax.cycad.sketch import Sketch, SketchPart
from cycax.spec import spec_hash


def build_volume(part, tmp_path) -> testing.Measure:
    result = cycax.build(part, outputs=["step"], backend="local", project_dir=tmp_path)
    target = next(iter(result.targets.values()))
    assert target.error is None, target.error
    return testing.measure(target.files["step"])


def test_pad_with_holes_pocket_and_boss(tmp_path):
    outline = Sketch().rectangle(0, 0, 80, 40, radius=5)
    for x in (10, 70):
        outline.circle(x, 20, diameter=4.2)
    plate = SketchPart(part_no="sk_plate", sketch=outline, thickness=3)
    plate.top.pocket(Sketch().rectangle(30, 10, 20, 20), depth=1)
    plate.front.boss(Sketch().slot(30, 1.5, length=20, width=2), height=5)
    spec = plate.export()
    assert [f["type"] for f in spec["features"]] == ["sketch", "sketch", "sketch"]
    measured = build_volume(plate, tmp_path)
    area = 80 * 40 - (4 - math.pi) * 25 - 2 * math.pi * 2.1**2
    assert measured.volume == pytest.approx(area * 3 - 400 * 1 + (40 + math.pi) * 5)
    assert measured.bbox_min == pytest.approx((0, -5, 0))


def test_revolve(tmp_path):
    # A 10 x 20 rectangle 5 mm from the y axis, revolved about it: a tube.
    part = SketchPart(
        part_no="tube", sketch=Sketch().rectangle(5, 0, 10, 20), revolve={"axis": [[0, 0], [0, 1]], "angle": 360}
    )
    measured = build_volume(part, tmp_path)
    assert measured.volume == pytest.approx(math.pi * (15**2 - 5**2) * 20, rel=1e-6)


def make_dxf(path, units=4):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = units
    msp = doc.modelspace()
    # A 60 x 30 outline with one rounded end (bulge 1 = a half circle), and 3 holes.
    msp.add_lwpolyline(
        [(0, 0, 0, 0, 0), (45, 0, 0, 0, 1), (45, 30, 0, 0, 0), (0, 30, 0, 0, 0)], format="xyseb", close=True
    )
    for x in (10, 20, 30):
        msp.add_circle((x, 15), radius=2)
    doc.saveas(path)


def test_dxf_outline_with_a_hole_pattern(tmp_path):
    dxf = tmp_path / "bracket.dxf"
    make_dxf(dxf)
    sketch = Sketch.from_dxf(dxf)
    assert sketch.source["file"] == "bracket.dxf"
    part = SketchPart(part_no="dxf_bracket", sketch=sketch, thickness=2)
    measured = build_volume(part, tmp_path)
    area = 45 * 30 + math.pi * 15**2 / 2 - 3 * math.pi * 2**2
    assert measured.volume == pytest.approx(area * 2, rel=1e-6)
    assert measured.bbox_max[0] == pytest.approx(60)


def test_dxf_units_and_scale(tmp_path):
    dxf = tmp_path / "inch.dxf"
    make_dxf(dxf, units=1)  # inches
    assert Sketch.from_dxf(dxf).bounds()[1][1] == pytest.approx(30 * 25.4)
    unitless = tmp_path / "none.dxf"
    make_dxf(unitless, units=0)
    with pytest.raises(ValueError, match="no units"):
        Sketch.from_dxf(unitless)
    assert Sketch.from_dxf(unitless, scale=1.0).bounds()[1][1] == pytest.approx(30)


def test_a_changed_dxf_changes_the_hash(tmp_path):
    dxf = tmp_path / "a.dxf"
    make_dxf(dxf)
    first = spec_hash(SketchPart(part_no="p", sketch=Sketch.from_dxf(dxf), thickness=2).export())
    doc = ezdxf.readfile(dxf)
    doc.modelspace().add_circle((40, 15), radius=2)
    doc.saveas(dxf)
    second = spec_hash(SketchPart(part_no="p", sketch=Sketch.from_dxf(dxf), thickness=2).export())
    assert first != second
