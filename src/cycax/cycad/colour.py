# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging

COLOUR_MAP: dict[str, list[float]] = {
    "orange": [1.0, 0.5, 0.0],
    "blue": [0.0, 0.0, 1.0],
    "red": [1.0, 0.0, 0.0],
    "green": [0.0, 1.0, 0.0],
    "yellow": [1.0, 1.0, 0.0],
    "purple": [0.5, 0.0, 0.5],
    "white": [1.0, 1.0, 1.0],
    "black": [0.0, 0.0, 0.0],
    "gray": [0.5, 0.5, 0.5],
    "grey": [0.5, 0.5, 0.5],
    "pink": [1.0, 0.753, 0.796],
}

DEFAULT_COLOUR = "orange"


def to_rgb(colour: str) -> list[float]:
    """Convert a colour name into an `[r, g, b]` float array (each 0.0-1.0).

    Args:
        colour: A colour name, e.g. "orange", "gray".

    Returns:
        `[r, g, b]`, each component a float between 0.0 and 1.0.
    """
    rgb = COLOUR_MAP.get(colour.lower())
    if rgb is None:
        logging.warning("Unknown colour name %s, using %s instead.", colour, DEFAULT_COLOUR)
        rgb = COLOUR_MAP[DEFAULT_COLOUR]
    return list(rgb)
