# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json

import pytest

from cycax.cycad import SheetMetalBend


def test_sheetmetal_defaults():
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    assert sheet.material == {"name": "mild-steel", "code": "1008", "standard": "AISI"}
    assert sheet.k_factor == 0.44
    assert sheet.bend_radius == 2.0  # defaults to thickness


def test_sheetmetal_overrides():
    material = {"name": "aluminium", "code": "5052-H32", "standard": "AISI"}
    sheet = SheetMetalBend(
        part_no="s", x_size=100.0, y_size=50.0, z_size=2.0, material=material, k_factor=0.42, bend_radius=3.0
    )
    assert sheet.material == material
    assert sheet.k_factor == 0.42
    assert sheet.bend_radius == 3.0


def test_root_bend_geometry_and_bounding_box():
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    wall = sheet.front.bend(angle=90, height=20.0)

    assert wall.width == 100.0
    assert wall.height == 20.0
    assert wall.origin == (0.0, 0.0, 2.0)
    assert wall.v_dir == (0.0, 0.0, 1.0)  # "up" -> extends fully in +Z
    assert (sheet.x_min, sheet.x_max) == (0.0, 100.0)
    # y_min goes to -2 (not 0): the wall's 2 mm thickness sits *outward* of the fold line
    # (y=0), the same way the base plate's own thickness sits *below* its top face -- a
    # clean, non-overlapping right-angle corner between base and wall.
    assert (sheet.y_min, sheet.y_max) == (-2.0, 50.0)
    assert (sheet.z_min, sheet.z_max) == (0.0, 22.0)


@pytest.mark.parametrize("side", ["front", "back", "left", "right"])
def test_bend_defaults_direction_to_up(side):
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    flange = getattr(sheet, side).bend(angle=90, height=10.0)
    feature = sheet.features[-1]
    assert feature.direction == "up"
    assert feature.angle == 90.0
    assert flange.v_dir == (0.0, 0.0, 1.0)


def test_negative_angle_flips_direction_through_bend():
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    sheet.front.bend(angle=-45, height=10.0)
    feature = sheet.features[-1]
    assert (feature.angle, feature.direction) == (45.0, "down")


def test_double_negative_cancels_through_bend():
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    sheet.front.bend(angle=-90, height=10.0, direction="down")
    feature = sheet.features[-1]
    assert (feature.angle, feature.direction) == (90.0, "up")


def test_bend_only_allowed_on_left_right_front_back():
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    for side in ("top", "bottom"):
        with pytest.raises(ValueError, match="LEFT, RIGHT, FRONT, or BACK"):
            getattr(sheet, side).bend(angle=90, height=10.0)


def test_second_independent_root_bend_starts_from_the_base_footprint_not_the_grown_bbox():
    """Regression test: a second root bend must not start from wherever a previous bend
    already grew the part's bounding box to (root_bend_side() used to read part.z_max,
    which drifts once a bend exists -- see cycax.cycad.bend.root_bend_side)."""
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    sheet.front.bend(angle=90, height=200.0)  # grows part.z_max to 202
    left_wall = sheet.left.bend(angle=90, height=10.0)
    assert left_wall.origin == (0.0, 0.0, 2.0)  # still the base's own thickness, not 202


def test_gap1_gap2_narrow_and_shift_the_flange():
    sheet = SheetMetalBend(part_no="s", x_size=80.0, y_size=50.0, z_size=3.0)
    flange = sheet.front.bend(angle=90, height=60.0, direction="down", gap1=10.0, gap2=10.0)
    assert flange.width == 60.0
    assert flange.origin == (10.0, 0.0, 3.0)


def test_gap_larger_than_width_raises():
    sheet = SheetMetalBend(part_no="s", x_size=80.0, y_size=50.0, z_size=3.0)
    with pytest.raises(ValueError, match="leaves no width"):
        sheet.front.bend(angle=90, height=60.0, gap1=50.0, gap2=50.0)


def test_nested_bend_parent_linkage_and_cumulative_angle():
    sheet = SheetMetalBend(part_no="s", x_size=440.0, y_size=89.0, z_size=2.0, k_factor=0.42, bend_radius=2.0)
    front_wall = sheet.front.bend(angle=90, height=200.0)
    front_lip = front_wall.far.bend(angle=90, height=10.0, direction="down")

    wall_feature, lip_feature = sheet.features[-2], sheet.features[-1]
    assert wall_feature.parent is None
    assert lip_feature.parent == wall_feature.id
    assert front_lip.origin == (0.0, 0.0, 202.0)
    # front_lip folds back "down" (toward the part) from a wall that went "up": net
    # cumulative angle is back to 0 -- the lip ends up flat again, pointing -Y like the
    # original unfolded base, just 202 mm up in Z.
    assert front_lip.v_dir == (0.0, -1.0, 0.0)


def test_three_stage_grip_cumulative_angle():
    sheet = SheetMetalBend(part_no="s", x_size=80.0, y_size=50.0, z_size=3.0, k_factor=0.42, bend_radius=3.0)
    grip = sheet.left.bend(angle=45, height=40.0)
    grip = grip.far.bend(angle=45, height=20.0)
    grip = grip.far.bend(angle=90, height=10.0)
    # 45 + 45 + 90 = 180 degrees -- the grip curls all the way back on itself.
    assert grip.v_dir == (1.0, 0.0, 0.0)


def test_far_is_an_alias_for_self():
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    wall = sheet.front.bend(angle=90, height=20.0)
    assert wall.far is wall


@pytest.mark.parametrize("edge", ["left", "right", "front", "back"])
def test_bending_off_a_flange_side_edge_is_not_yet_implemented(edge):
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    wall = sheet.front.bend(angle=90, height=20.0)
    with pytest.raises(NotImplementedError, match="not yet implemented"):
        getattr(wall, edge)


def test_round_corners_marks_terminal_and_blocks_further_bend():
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    wall = sheet.front.bend(angle=90, height=20.0)
    wall.round_corners(radius=3.0)

    feature = sheet.features[-1]
    assert feature.name == "flange_corner_round"
    assert feature.radius == 3.0
    assert feature.parent == sheet.features[-2].id

    with pytest.raises(ValueError, match="already been rounded"):
        wall.bend(angle=90, height=5.0)


def test_round_corners_needs_an_actual_bend():
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    root = sheet.front  # a plain CycadSide, not a bent flange -- has no round_corners()
    assert not hasattr(root, "round_corners")


def test_hole_on_axis_aligned_flange():
    sheet = SheetMetalBend(part_no="s", x_size=80.0, y_size=50.0, z_size=3.0)
    flange = sheet.front.bend(angle=90, height=60.0, direction="down", gap1=10.0, gap2=10.0)
    flange.hole(pos=(30.0, 30.0), diameter=13.0)

    holes = [f for f in sheet.features if f.name == "flange_hole_cut"]
    assert len(holes) == 1
    assert holes[0].diameter == 13.0
    assert holes[0].thickness == 3.0  # defaults to sheet thickness


def test_hole_on_non_axis_aligned_flange_raises():
    sheet = SheetMetalBend(part_no="s", x_size=80.0, y_size=50.0, z_size=3.0)
    grip = sheet.left.bend(angle=45, height=40.0)
    with pytest.raises(NotImplementedError, match="axis-aligned"):
        grip.hole(pos=(5.0, 5.0), diameter=3.0)


def test_export_is_json_serialisable_and_carries_bend_metadata():
    sheet = SheetMetalBend(
        part_no="tray",
        x_size=440.0,
        y_size=89.0,
        z_size=2.0,
        material={"name": "aluminium", "code": "5052-H32"},
        k_factor=0.42,
        bend_radius=2.0,
    )
    wall = sheet.front.bend(angle=90, height=200.0)
    wall.far.bend(angle=90, height=10.0, direction="down")

    data = sheet.export()
    encoded = json.dumps(data)  # must not raise
    decoded = json.loads(encoded)
    bend_features = [f for f in decoded["features"] if f["type"] == "bend"]
    assert len(bend_features) == 2
    for feature in bend_features:
        for key in (
            "angle",
            "direction",
            "radius",
            "k_factor",
            "gap1",
            "gap2",
            "corner_reference",
            "length_spec",
            "label",
            "parent",
            "id",
            "u_dir",
            "v_dir",
            "n_dir",
        ):
            assert key in feature
    assert bend_features[0]["parent"] is None
    assert bend_features[1]["parent"] == bend_features[0]["id"]


def test_geometry_is_free_of_sin_cos_float_noise_at_90_degrees():
    """Regression check: math.sin(pi/2)-style noise (e.g. 6.1e-17) must be cleaned up."""
    sheet = SheetMetalBend(part_no="s", x_size=100.0, y_size=50.0, z_size=2.0)
    wall = sheet.front.bend(angle=90, height=20.0)
    assert wall.v_dir == (0.0, 0.0, 1.0)
    assert wall.n_dir == (0.0, 1.0, 0.0)
    for value in (*wall.v_dir, *wall.n_dir, *wall.origin):
        assert repr(value) != "-0.0"
