# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from cycax.cycad.bend import resolve_bend_angle


@pytest.mark.parametrize(
    ("angle", "direction", "expected"),
    [
        # No direction given -> defaults to "up".
        (90, None, (90.0, "up")),
        (45, None, (45.0, "up")),
        (0, None, (0.0, "up")),
        (180, None, (180.0, "up")),
        # Direction explicitly given, positive angle -> unchanged.
        (90, "up", (90.0, "up")),
        (90, "down", (90.0, "down")),
        (45, "down", (45.0, "down")),
        # Negative angle with no direction given -> flips the "up" default to "down".
        (-45, None, (45.0, "down")),
        (-90, None, (90.0, "down")),
        (-180, None, (180.0, "down")),
        # Negative angle with an explicit direction -> flips that direction.
        (-45, "up", (45.0, "down")),
        # Two negatives cancel: explicit "down" + negative angle -> "up".
        (-90, "down", (90.0, "up")),
        (-45, "down", (45.0, "up")),
        # direction is case-insensitive.
        (90, "UP", (90.0, "up")),
        (90, "Down", (90.0, "down")),
        (-90, "DOWN", (90.0, "up")),
    ],
)
def test_resolve_bend_angle(angle, direction, expected):
    assert resolve_bend_angle(angle, direction) == expected


@pytest.mark.parametrize("angle", [181, 180.01, -181, -200, 360])
def test_resolve_bend_angle_rejects_more_than_180_degrees(angle):
    with pytest.raises(ValueError, match="exceeds the maximum bend angle"):
        resolve_bend_angle(angle)


def test_resolve_bend_angle_allows_exactly_180_degrees():
    assert resolve_bend_angle(180) == (180.0, "up")
    assert resolve_bend_angle(-180) == (180.0, "down")


@pytest.mark.parametrize("direction", ["sideways", "top", "", "u"])
def test_resolve_bend_angle_rejects_invalid_direction(direction):
    with pytest.raises(ValueError, match="is not one of"):
        resolve_bend_angle(90, direction)
