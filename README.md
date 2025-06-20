<!--
SPDX-FileCopyrightText: 2025 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# CyCAx

[![PyPI - Version](https://img.shields.io/pypi/v/cycax.svg)](https://pypi.org/project/cycax)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cycax.svg)](https://pypi.org/project/cycax)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

CyCAx is a Python package that provides a set of tools for working with CAD models.
CyCAx is not a CAD kernel nor does it attempt to be one.
It is designed to work with existing Opensource CAD tools and provide an interface for working with them - a way to combine the tools.

## Installation

Add `"cycax @ git+https://github.com/tsolo-io/cycax"` to your `pyproject.toml` file dependencies.

## Integrations

CyCAx provides integration with the following CAD tools:

- [OpenSCAD](https://github.com/openscad/openscad) for parts and assemblies
- [FreeCAD](https://github.com/FreeCAD/FreeCAD) for parts via [CyCAx Server](https://github.com/tsolo-io/cycax-server) and the [CyCAx FreeCAD Worker](https://github.com/tsolo-io/cycax-freecad-worker)
- [Blender](https://blender.org) for parts and assemblies  via [CyCAx Server](https://github.com/tsolo-io/cycax-server) and the [CyCAx Blender Worker](https://github.com/tsolo-io/cycax-blender-worker)

## Future

Add support for more CAD tools.
Example of this would be to add [build123d](https://github.com/build123d/build123d) as a 3D modeling library.
And Matplotlib as a 2D visualization library.

The integration in CAM tools for slicing for 3D printing and creation of g-code for CNC milling are also an objective.

## License

`CyCAx` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.
