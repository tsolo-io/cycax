# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Files that `cycax init` and `cycax new` write."""

import re

CYCAX_TOML = """\
# CyCAx project settings. Personal settings (tool paths, editor) go in the user config file.
[project]
name = "{name}"
sources = ["parts", "assemblies"]

[build]
backend = "{backend}"    # auto: this computer first, then the server | local | server
outputs = ["step"]       # FCStd, SCAD and the unfold DXF are added when the engine makes them
folder = "build"
# engine = "build123d"   # default engine for parts and assemblies
# profile = "standard"   # draft | standard | fine

[server]
url = "nats://127.0.0.1:4222"
"""

GITIGNORE = """\
build/
__pycache__/
.venv/
"""

PART = '''\
"""{title}."""

from cycax import cycax_part
from cycax.cycad import Print3D


@cycax_part
def {name}() -> Print3D:
    """{title}: a 40 x 20 x 5 mm plate with one hole."""
    # All sizes are in millimetres.
    part = Print3D(part_no="{name}", x_size=40, y_size=20, z_size=5)
    # A 4.2 mm hole through the plate, 10 mm from the left and 10 mm from the front.
    part.top.hole(pos=(10, 10), diameter=4.2)
    return part
'''

ASSEMBLY = '''\
"""{title}."""

from cycax import cycax_assembly
from cycax.cycad import Assembly, Print3D


@cycax_assembly
def {name}() -> Assembly:
    """{title}: two plates, one on top of the other."""
    assembly = Assembly("{name}")
    base = Print3D(part_no="{name}_base", x_size=40, y_size=20, z_size=5)
    top = Print3D(part_no="{name}_top", x_size=40, y_size=20, z_size=3)
    assembly.add(base)
    assembly.add(top)
    # Put the bottom of the top plate on the top of the base plate.
    top.level(bottom=base.top)
    return assembly
'''

TEMPLATES = {"part": ("parts", PART), "assembly": ("assemblies", ASSEMBLY)}


def slug(text: str) -> str:
    """A valid Python name from free text: "PSU Bracket" -> "psu_bracket"."""
    name = re.sub(r"\W+", "_", text.strip().lower()).strip("_")
    return f"_{name}" if name[:1].isdigit() else name or "part"


def render(kind: str, name: str) -> tuple[str, str]:
    """(folder, file content) for a new part or assembly."""
    folder, template = TEMPLATES[kind]
    return folder, template.format(name=slug(name), title=name.replace("_", " ").capitalize())
