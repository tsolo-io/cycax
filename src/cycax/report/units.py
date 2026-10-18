# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Units on report pages (plan P2.5): a fixed ladder per quantity, no litres.

summary.json keeps g and mm³; the pages show g/kg/t and mm³/cm³/dm³/m³. (A fixed ladder in
plain Python gives the same text as pint would, without one more dependency.)
"""

MASS = (("t", 1e6), ("kg", 1e3), ("g", 1.0))
VOLUME = (("m³", 1e9), ("dm³", 1e6), ("cm³", 1e3), ("mm³", 1.0))
AREA = (("m²", 1e6), ("cm²", 1e2), ("mm²", 1.0))


def _ladder(value: float, ladder) -> str:
    for unit, factor in ladder:
        if abs(value) >= factor or factor == 1.0:
            return f"{value / factor:.3g} {unit}"
    return f"{value:.3g}"  # pragma: no cover


def mass(grams: float) -> str:
    return _ladder(grams, MASS)


def volume(mm3: float) -> str:
    return _ladder(mm3, VOLUME)


def area(mm2: float) -> str:
    return _ladder(mm2, AREA)


def length(mm: float) -> str:
    return f"{mm:g} mm"
