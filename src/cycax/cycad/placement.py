# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""4 x 4 placement matrices in plain Python (task cycax/32).

A part's placement maps its own coordinates (the part as it was designed, at the origin) to
the world. Row-major, `[[r00, r01, r02, tx], [r10, r11, r12, ty], [r20, r21, r22, tz], [0, 0, 0, 1]]`,
lengths in mm. Rotations are counter-clockwise when you look along the axis towards the origin
(right-hand rule), in degrees.
"""

import math

Matrix = list[list[float]]


def identity() -> Matrix:
    return [[1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]


def translation(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Matrix:
    m = identity()
    m[0][3], m[1][3], m[2][3] = float(x), float(y), float(z)
    return m


EXACT = 1e-12


def _clean(value: float) -> float:
    """Exact 0/±1 for quarter turns (cos 90° is 6e-17 otherwise)."""
    for exact in (0.0, 1.0, -1.0):
        if abs(value - exact) < EXACT:
            return exact
    return value


def rotation(axis: str, degrees: float) -> Matrix:
    a = math.radians(degrees)
    c, s = _clean(math.cos(a)), _clean(math.sin(a))
    m = identity()
    i, j = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[axis]
    m[i][i], m[i][j], m[j][i], m[j][j] = c, -s, s, c
    return m


def multiply(a: Matrix, b: Matrix) -> Matrix:
    """a @ b: first b, then a."""
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def apply(m: Matrix, point) -> tuple[float, float, float]:
    x, y, z = point
    return tuple(m[r][0] * x + m[r][1] * y + m[r][2] * z + m[r][3] for r in range(3))


def bounds(m: Matrix, lo, hi) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """The axis-aligned box of the 8 transformed corners of the box lo..hi."""
    corners = [apply(m, (x, y, z)) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
    return (
        tuple(min(c[i] for c in corners) for i in range(3)),
        tuple(max(c[i] for c in corners) for i in range(3)),
    )


def about(centre, m: Matrix) -> Matrix:
    """`m` applied about `centre` instead of the origin."""
    return multiply(translation(*centre), multiply(m, translation(*(-v for v in centre))))


def is_quarter_turns(m: Matrix) -> bool:
    """True when the rotation part only swaps and flips axes (multiples of 90 degrees)."""
    return all(m[r][c] in (0.0, 1.0, -1.0) for r in range(3) for c in range(3))
