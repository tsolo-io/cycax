# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

from cycax.cycad.engines.base_assembly_engine import AssemblyEngine


class AssemblyBlender(AssemblyEngine):
    """Assemble the parts into an Blender model.

    Args:
        name: The part number of the complex part that is being assembled.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        msg = "Local Blender assemblies were removed. Use the cycax-blender-worker (via NATS)."
        raise NotImplementedError(msg)
