# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import build123d

from cycax.cycad import SheetMetalBend
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


def _render(part, tmp_path: Path) -> build123d.Shape:
    part.save(path=tmp_path)
    engine = PartEngineBuild123d(name=part.part_no, path=tmp_path)
    files = part.build(engine)
    stl_files = [f["file"] for f in files if f["file"].suffix == ".stl"]
    assert len(stl_files) == 1
    return build123d.import_stl(str(stl_files[0]))


def test_render_tray_with_return_lip_and_outward_tips(tmp_path: Path):
    """The bend.py example: 90-degree bends only, one nested "fold back" (front_lip) and
    two nested "keep curling the same way" (left/right tips), corners rounded on the tips.
    """
    tray = SheetMetalBend(
        part_no="aluminium_tray", x_size=440.0, y_size=89.0, z_size=2.0, k_factor=0.42, bend_radius=2.0
    )
    tray.back.bend(angle=90, height=200.0)
    front_wall = tray.front.bend(angle=90, height=200.0)
    front_wall.far.bend(angle=90, height=10.0, direction="down")
    left_wall = tray.left.bend(angle=90, height=200.0)
    left_tip = left_wall.far.bend(angle=90, height=30.0)
    right_wall = tray.right.bend(angle=90, height=200.0)
    right_tip = right_wall.far.bend(angle=90, height=30.0)
    left_tip.round_corners(radius=6.0)
    right_tip.round_corners(radius=6.0)

    shape = _render(tray, tmp_path)
    bbox = shape.bounding_box()
    # Base footprint (440x89) grows by the two 2 mm side-wall thicknesses in X, and the
    # front lip's 10 mm reach in -Y; height reaches base + 200 mm wall + 30 mm tip's own
    # thickness sitting on top once it's folded flat.
    assert abs(bbox.size.X - 444.0) < 0.01
    assert abs(bbox.size.Y - 101.0) < 0.01
    assert abs(bbox.size.Z - 204.0) < 0.01


def test_render_bracket_with_gap_narrowed_flanges_and_grip_curl(tmp_path: Path):
    """The bend2.py example: gap1/gap2-narrowed flanges bent "down", and a 3-stage
    same-direction 45/45/90 curl -- the first non-90-degree bend geometry exercised."""
    bracket = SheetMetalBend(
        part_no="aluminium_bracket", x_size=80.0, y_size=50.0, z_size=3.0, k_factor=0.42, bend_radius=3.0
    )
    bracket.top.hole(pos=(40.0, 25.0), diameter=30.0)

    front_flange = bracket.front.bend(angle=90, height=60.0, direction="down", gap1=10.0, gap2=10.0)
    front_flange.round_corners(radius=6.0)
    front_flange.hole(pos=(30.0, 30.0), diameter=13.0)

    back_flange = bracket.back.bend(angle=90, height=60.0, direction="down", gap1=10.0, gap2=10.0)
    back_flange.round_corners(radius=6.0)
    back_flange.hole(pos=(30.0, 30.0), diameter=13.0)

    left_grip = bracket.left.bend(angle=45, height=40.0)
    left_grip = left_grip.far.bend(angle=45, height=20.0)
    left_grip.far.bend(angle=90, height=10.0)

    right_grip = bracket.right.bend(angle=45, height=40.0)
    right_grip = right_grip.far.bend(angle=45, height=20.0)
    right_grip.far.bend(angle=90, height=10.0)

    shape = _render(bracket, tmp_path)
    bbox = shape.bounding_box()
    # Sanity bounds only (exact float geometry through a 45-degree fold isn't worth
    # hand-deriving here) -- mainly this must render at all without a ShapeList/export
    # failure, and be roughly the right size, not e.g. collapsed to zero or exploded.
    assert 100.0 < bbox.size.X < 200.0
    assert abs(bbox.size.Y - 50.0) < 0.01
    assert 100.0 < bbox.size.Z < 180.0


def test_render_single_bend_no_nesting(tmp_path: Path):
    """A minimal case: one bend, no nesting, no gaps -- the simplest possible render."""
    sheet = SheetMetalBend(part_no="simple", x_size=50.0, y_size=30.0, z_size=1.5)
    sheet.front.bend(angle=90, height=15.0)

    shape = _render(sheet, tmp_path)
    bbox = shape.bounding_box()
    assert abs(bbox.size.X - 50.0) < 0.01
    assert abs(bbox.size.Z - 16.5) < 0.01  # 1.5 mm base + 15 mm wall
