# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad.assembly import Assembly  # noqa: F401
from cycax.cycad.cuboid import Cuboid, Print3D, SheetMetal  # noqa: F401
from cycax.cycad.cycad_part import CycadPart  # noqa: F401
from cycax.targets import cycax_assembly, cycax_part  # noqa: F401
# from cycax.cycad.cycad_side import BackSide, BottomSide, FrontSide, LeftSide, RightSide, TopSide


def build(*targets, **kwargs):
    """Build parts and assemblies. See `cycax.api.build` (imported on first use: fast start)."""
    from cycax.api import build as _build  # noqa: PLC0415

    return _build(*targets, **kwargs)
