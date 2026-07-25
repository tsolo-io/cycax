# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Example demonstrating the unified Engine API.

This example shows how to use the unified EngineFreeCAD and EngineOpenSCAD
classes to build both parts and assemblies from JSON files.
"""

from pathlib import Path

from cycax.cycad import EngineFreeCAD, EngineOpenSCAD


def build_with_openscad():
    """Build parts and assemblies using the unified OpenSCAD engine."""

    engine = EngineOpenSCAD()

    # Build directory contains both part and assembly JSON files
    build_dir = Path("./build")

    if not build_dir.exists():
        return

    # Find some JSON files to build
    json_files = []

    # Look for a part JSON
    part_jsons = list(build_dir.glob("**/gear_*.json"))
    if part_jsons:
        json_files.append(part_jsons[0])

    # Look for an assembly JSON
    assembly_jsons = list(build_dir.glob("**/box.json"))
    if assembly_jsons:
        json_files.append(assembly_jsons[0])

    if json_files:
        # Build all files in one call - engine auto-detects parts vs assemblies
        artifacts = engine.build(json_files)

        for _artifact in artifacts:
            pass
    else:
        pass


def build_with_freecad():
    """Build parts and assemblies using the unified FreeCAD engine."""

    # Configure output formats
    config = {
        "out_formats": "STL,PNG",
        # Optionally specify FreeCAD path:
        # "freecad_app": "/path/to/FreeCAD.AppImage"
    }

    engine = EngineFreeCAD(config=config)

    build_dir = Path("./build")

    if not build_dir.exists():
        return

    # Find JSON files
    json_files = []

    part_jsons = list(build_dir.glob("**/gear_*.json"))
    if part_jsons:
        json_files.append(part_jsons[0])

    if json_files:
        # Build - artifacts placed in same directory as JSON files
        engine.build(json_files)


if __name__ == "__main__":
    # Build with OpenSCAD
    build_with_openscad()

    # Build with FreeCAD (requires FreeCAD to be installed)
    # Uncomment to test:
    # build_with_freecad()
