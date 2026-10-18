<!--
SPDX-FileCopyrightText: 2025, 2026 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# CAD Tool Integrations

CyCAx supports multiple CAD tools through two integration approaches: **Direct** and **Server-based**. This guide explains how to set up and use each integration.

## Integration Overview

| CAD Tool | Parts (Direct) | Assemblies (Direct) | Parts (Server) | Assemblies (Server) |
|----------|----------------|---------------------|----------------|-------------------|
| [OpenSCAD](https://openscad.org) | ✅ | ✅ | ❌ | ❌ |
| [build123d](https://github.com/gumyr/build123d) | ✅ | ✅ | ❌ | ❌ |
| [FreeCAD](https://freecad.org) | ✅ | ❌ | ✅ | ❌ |
| [Blender](https://blender.org) | ❌ | ❌ | ❌ | ✅ |

## Direct Integrations

Direct integrations run CAD tools locally on your machine.

### OpenSCAD Integration

OpenSCAD is the most mature integration, perfect for parametric modeling.

**Installation:**
```bash
# Ubuntu/Debian
sudo apt install openscad

# macOS
brew install openscad

# Windows: Download from openscad.org
```

**Usage:**
```python
from cycax.cycad import Print3D, Assembly

class OpenSCADPart(Print3D):
    def __init__(self):
        super().__init__(part_no="scad_part", x_size=30, y_size=20, z_size=10)

# Render with OpenSCAD (default for most operations)
part = OpenSCADPart()
part.render()  # Uses OpenSCAD by default
part.render(engine="openscad")  # Explicit

# For assemblies
assembly = Assembly("my_assembly")
assembly.render(engine="openscad")
```

**Features:**
- Excellent for parametric designs
- Fast rendering
- Great for boolean operations
- STL export support

### build123d Integration

build123d is a modern Python-native CAD library with excellent Python integration.

**Installation:**
build123d is automatically installed with CyCAx - no additional setup needed!

**Usage:**
```python
from cycax.cycad import Print3D
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d

class Build123dPart(Print3D):
    def __init__(self):
        super().__init__(part_no="b123d_part", x_size=25, y_size=25, z_size=15)

part = Build123dPart()
part.build(PartEngineBuild123d())  # build123d is not a render() option

# For assemblies with custom engine configuration
assembly = Assembly("build123d_assembly")
assembly.build(
    engine=AssemblyBuild123d(assembly.name),
    part_engines=[PartEngineBuild123d()]
)
```

**Features:**
- Pure Python implementation
- Modern CAD kernel
- Excellent for programmatic design
- STEP, STL, and other format support
- No external dependencies

### FreeCAD Integration

FreeCAD provides professional CAD features for parts (assemblies require server integration).

**Installation:**
```bash
# Ubuntu/Debian
sudo apt install freecad

# macOS
brew install freecad

# Windows: Download from freecad.org
```

**Usage:**
```python
from cycax.cycad import Print3D

class FreeCADPart(Print3D):
    def __init__(self):
        super().__init__(part_no="freecad_part", x_size=40, y_size=30, z_size=20)

part = FreeCADPart()
part.render(engine="freecad")
```

**Features:**
- Professional CAD capabilities
- Advanced constraint solving
- Multiple export formats
- Parametric modeling
- Assembly workbench (via server integration)

## Server-Based Integrations

Remote builds go through NATS: the CyCAx workers (`cycax-freecad-worker`,
`cycax-blender-worker`) take tasks from NATS and put the results into the NATS object-store
cache. `cycax-server` is optional (cache browser, clean-up, metrics). The old HTTP server
engines (`PartEngineServer`, `AssemblyServer`) were removed.

- Run the stack locally: `make build && make start` in the CyCAx workspace
  (`cycax-server/deployment/compose.yaml`).
- Send one compiled part or assembly by hand: `cycax-send <worker_kind> <json_file>`
  (in `cycax-server`).
- The CLI: `cycax build --server` (see [The cycax command](cli.md)).

## Engine Selection Guide

Choose the right engine based on your needs:

### For Beginners
- **OpenSCAD**: Easy to start, good documentation
- **build123d**: Modern Python approach, no external dependencies

### For Advanced Users
- **FreeCAD**: Professional features, constraint solving
- **Blender**: Advanced visualization, photorealistic rendering

### For Production
- **OpenSCAD**: Reliable, fast, well-tested
- **build123d**: Pure Python, easy deployment
- **FreeCAD Server**: Professional features with server scaling

## Engine Configuration

### Custom Engine Settings

```python
from cycax.cycad.engines.part_openscad import PartEngineOpenSCAD

# Configure OpenSCAD engine
engine_config = {
    "resolution": 100,      # Render quality
    "preview": False,       # Final render vs preview
    "output_format": "stl"  # Output format
}

part.render(engine="openscad", engine_config=engine_config)
```

### Assembly Engine Configuration

```python
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d

# Custom assembly configuration
assembly_engine = AssemblyBuild123d(
    name="my_assembly",
    output_format="step",  # STEP format instead of STL
    combine_parts=True     # Combine all parts into single file
)

assembly.build(engine=assembly_engine)
```

## Multi-Engine Workflows

You can use different engines for different parts:

```python
from cycax.cycad import Assembly, Print3D

class ParametricPart(Print3D):
    def __init__(self):
        super().__init__(part_no="param_part", x_size=30, y_size=20, z_size=10)

class PrecisionPart(Print3D):
    def __init__(self):
        super().__init__(part_no="precision_part", x_size=25, y_size=25, z_size=15)

assembly = Assembly("mixed_assembly")
param_part = ParametricPart()
precision_part = PrecisionPart()

# Use different engines for different parts
param_part.render(engine="openscad")      # Fast parametric
precision_part.build(PartEngineBuild123d())  # High precision (build123d)

assembly.add(param_part, "param")
assembly.add(precision_part, "precision")
assembly.render()  # Final assembly render
```

## Troubleshooting

### Common Issues

**OpenSCAD not found:**
```bash
# Check if OpenSCAD is in PATH
openscad --version

# Ubuntu: Add to PATH if needed
export PATH=$PATH:/usr/bin
```

**build123d import errors:**
```bash
# Reinstall build123d
pip install --force-reinstall build123d
```

**FreeCAD Python module not found:**
```bash
# Ubuntu: Install FreeCAD dev packages
sudo apt install freecad-python3

# Or use AppImage version
```

**Server connection issues:** the workers need a reachable NATS (`CYCAX_NATS_URL`, default
`nats://127.0.0.1:4222`). Check that the `nats` service of the stack is running.

### Performance Tips

**OpenSCAD Optimization:**
```python
# Use lower resolution for development
part.render(engine="openscad", engine_config={"resolution": 50})

# Higher resolution for final output  
part.render(engine="openscad", engine_config={"resolution": 200})
```

**build123d Optimization:**
```python
# Enable parallel processing for complex assemblies
assembly.build(
    engine=AssemblyBuild123d(assembly.name),
    parallel=True
)
```

## Next Steps

- **[Examples](examples.md)**: See integration examples in action
- **[API Reference](api/index.md)**: Detailed engine API documentation
- **[Parts Guide](parts.md)**: Advanced part creation with different engines
