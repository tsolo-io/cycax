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
    "silver": [0.753, 0.753, 0.753],
    "lightgray": [0.827, 0.827, 0.827],
    "lightgrey": [0.827, 0.827, 0.827],
    "darkgray": [0.663, 0.663, 0.663],
    "darkgrey": [0.663, 0.663, 0.663],
    "navy": [0.0, 0.0, 0.502],
    "teal": [0.0, 0.502, 0.502],
    "olive": [0.502, 0.502, 0.0],
    "maroon": [0.502, 0.0, 0.0],
    "lime": [0.0, 1.0, 0.0],
    "cyan": [0.0, 1.0, 1.0],
    "aqua": [0.0, 1.0, 1.0],
    "magenta": [1.0, 0.0, 1.0],
    "fuchsia": [1.0, 0.0, 1.0],
    "brown": [0.647, 0.165, 0.165],
    "beige": [0.961, 0.961, 0.863],
    "gold": [1.0, 0.843, 0.0],
    "tan": [0.824, 0.706, 0.549],
}

DEFAULT_COLOUR = "orange"


def to_rgb(colour: str | list[float] | tuple[float, float, float]) -> list[float]:
    """Convert a colour name into an `[r, g, b]` float array (each 0.0-1.0).

    Args:
        colour: A colour name ("orange", "silver", ...), hex ("#ff8800", "#f80"), or an RGB
            sequence (0.0-1.0, or 0-255).

    Returns:
        `[r, g, b]`, each component a float between 0.0 and 1.0.
    """
    if isinstance(colour, list | tuple):
        values = [float(c) for c in colour]
        if any(v > 1.0 for v in values):  # 0-255 values
            values = [v / 255.0 for v in values]
        return values
    if colour.startswith("#") and len(colour) in (4, 7):
        digits = colour[1:]
        if len(digits) == 3:  # noqa: PLR2004 - "#rgb"
            digits = "".join(c * 2 for c in digits)
        try:
            return [round(int(digits[i : i + 2], 16) / 255.0, 3) for i in (0, 2, 4)]
        except ValueError:
            pass
    rgb = COLOUR_MAP.get(colour.lower())
    if rgb is None:
        logging.warning("Unknown colour name %s, using %s instead.", colour, DEFAULT_COLOUR)
        rgb = COLOUR_MAP[DEFAULT_COLOUR]
    return list(rgb)
