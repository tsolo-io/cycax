# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
from pathlib import Path

from cycax.cycad.engines.base_engine import Engine
from cycax.cycad.engines.part_openscad import PartEngineOpenSCAD


class EngineOpenSCAD(Engine):
    """Unified OpenSCAD engine for building both parts and assemblies.

    This engine can process JSON files containing either part definitions
    (with "features") or assembly definitions (with "parts") and build
    them using OpenSCAD.

    Attributes:
        config: Configuration dictionary for the engine.
    """

    def __init__(self, config: dict | None = None):
        """Initialize the OpenSCAD engine.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config)
        self.engine_name = "OpenSCAD"

    def build_part(self, json_file: Path) -> list[dict]:
        """Build a part using OpenSCAD.

        Args:
            json_file: Path to the part JSON file.

        Returns:
            List of generated file information dictionaries.
        """
        json_path = Path(json_file).expanduser().resolve().absolute()
        data = self.load_json(json_path)
        name = data.get("name", json_path.stem)
        base_path = json_path.parent.parent

        # Check if features exist
        if not data.get("features"):
            logging.warning(f"No features found in part JSON: {json_path}")
            return []

        # Use existing PartEngineOpenSCAD
        engine = PartEngineOpenSCAD(name=name, path=base_path)
        engine._json_file = json_path

        try:
            files = engine.build(None)
            for file_info in files:
                logging.info(f"Created {file_info['type']} file: {file_info['file']}")
            return files
        except Exception as error:
            logging.error(f"Error building OpenSCAD part {name}: {error}")
            return []

    def build_assembly(self, json_file: Path) -> list[dict]:
        """Build an assembly using OpenSCAD.

        Args:
            json_file: Path to the assembly JSON file.

        Returns:
            List of generated file information dictionaries.
        """
        json_path = Path(json_file).expanduser().resolve().absolute()
        data = self.load_json(json_path)
        name = data.get("name", json_path.stem)
        base_path = json_path.parent

        # Check if parts exist
        if not data.get("parts"):
            logging.warning(f"No parts found in assembly JSON: {json_path}")
            return []

        # Import here to avoid circular dependencies
        from cycax.cycad.assembly_openscad import AssemblyOpenSCAD  # noqa: PLC0415

        # Build each part first
        for part_data in data["parts"]:
            part_no = part_data["name"]
            part_json = base_path / part_no / f"{part_no}.json"

            if part_json.exists():
                logging.info(f"Building part {part_no} for assembly {name}")
                self.build_part(part_json)
            else:
                logging.warning(f"Part JSON not found: {part_json}")

        # Now build the assembly
        engine = AssemblyOpenSCAD(name=name)
        engine.set_path(base_path)
        engine._json_file = json_path

        for part in data["parts"]:
            engine.add(part)

        try:
            engine.build(base_path)
            logging.info(f"Created assembly SCAD file: {name}.scad")

            # Return list of generated files
            files = [
                {"file": base_path / f"{name}.scad", "description": "OpenSCAD assembly file"},
            ]

            return self.file_list(files, self.engine_name, score=3)

        except Exception as error:
            logging.error(f"Error building OpenSCAD assembly {name}: {error}")
            return []
