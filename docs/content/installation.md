<!--
SPDX-FileCopyrightText: 2025 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Installation

This guide will help you install CyCAx and its dependencies.

## Requirements

- **Python**: 3.10 or higher
- **Operating System**: Linux, macOS, or Windows

## Installation Methods

### Method 1: Install from Git (Recommended)

Add CyCAx to your project's `pyproject.toml`:

```toml
[project]
dependencies = [
    "cycax @ git+https://github.com/tsolo-io/cycax"
]
```

Then install with pip:

```bash
pip install "cycax @ git+https://github.com/tsolo-io/cycax"
```

### Method 2: Development Installation

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/tsolo-io/cycax.git
cd cycax

# Install with hatch (recommended for development)
pip install hatch
hatch shell

# Or install in development mode
pip install -e .
```

## CAD Tool Dependencies

CyCAx integrates with various CAD tools. Install the ones you plan to use:

### OpenSCAD (Recommended)

OpenSCAD is the most mature integration and works great for parametric modeling.

**Ubuntu/Debian:**
```bash
sudo apt install openscad
```

**macOS:**
```bash
brew install openscad
```

**Windows:**
Download from [OpenSCAD.org](https://openscad.org/downloads.html)

### build123d

build123d is a modern Python-native CAD library that's automatically installed with CyCAx.

No additional installation needed - it's included in CyCAx dependencies.

### FreeCAD (Optional)

For advanced CAD features:

**Ubuntu/Debian:**
```bash
sudo apt install freecad
```

**macOS:**
```bash
brew install freecad
```

**Windows:**
Download from [FreeCAD.org](https://www.freecad.org/downloads.php)

## Verification

Verify your installation by creating a simple test:

```python
# test_installation.py
from cycax.cycad import Assembly, Print3D

class TestPart(Print3D):
    def __init__(self):
        super().__init__(part_no="test", x_size=10, y_size=10, z_size=10)

# Test assembly creation
assembly = Assembly("test_assembly")
part = TestPart()
assembly.add(part, "test_part")
print("CyCAx installation successful!")
```

Run the test:

```bash
python test_installation.py
```

## Troubleshooting

### Common Issues

**Import Error: No module named 'cycax'**
- Ensure you've installed CyCAx in the correct Python environment
- Try `pip list | grep cycax` to verify installation

**OpenSCAD not found**
- Ensure OpenSCAD is installed and in your PATH
- Try running `openscad --version` in your terminal

**Permission errors on Linux**
- You may need to install additional packages: `sudo apt install python3-dev build-essential`

**Build123d import errors**
- Ensure you have Python 3.10+ installed
- Try reinstalling with: `pip install --force-reinstall cycax`

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/tsolo-io/cycax/issues)
2. Create a new issue with your system details and error message
3. Include the output of `pip list | grep -E "(cycax|build123d)"` in your report

## Next Steps

Now that you have CyCAx installed, continue to the [Getting Started](getting-started.md) guide to create your first project.
