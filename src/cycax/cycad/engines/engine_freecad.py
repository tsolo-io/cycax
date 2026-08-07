# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import subprocess
from pathlib import Path

from cycax.cycad.engines.base_engine import Engine
from cycax.cycad.location import TOP


class EngineFreeCAD(Engine):
    """Unified FreeCAD engine for building both parts and assemblies.

    This engine can process JSON files containing either part definitions
    (with "features") or assembly definitions (with "parts") and build
    them using FreeCAD.

    Attributes:
        config: Configuration dictionary supporting:
            - freecad_app: Path to FreeCAD binary (optional)
            - out_formats: Output formats (default: "STL,PNG")
    """

    def __init__(self, config: dict | None = None):
        """Initialize the FreeCAD engine.

        Args:
            config: Optional configuration dictionary.
        """
        super().__init__(config)
        self.engine_name = "FreeCAD"

    def get_freecad_app(self, base_path: Path | None = None) -> Path:
        """Get the FreeCAD application binary path.

        Args:
            base_path: Optional base path to search for FreeCAD.

        Returns:
            Path to FreeCAD binary.

        Raises:
            FileNotFoundError: If FreeCAD binary cannot be found.
        """
        # Check if specified in config
        if self.config.get("freecad_app"):
            app_path = Path(self.config["freecad_app"])
            if app_path.exists():
                return app_path

        # Search common locations for AppImage
        search_paths = [
            Path("~/Applications").expanduser(),
            Path.home() / "Applications",
        ]

        if base_path:
            search_paths.append(base_path)

        for search_path in search_paths:
            if search_path.exists():
                for appimg in search_path.glob("FreeCAD*.AppImage"):
                    logging.info(f"Found FreeCAD AppImage: {appimg}")
                    return appimg

        msg = "FreeCAD binary not found. Please specify 'freecad_app' in config or install FreeCAD AppImage."
        raise FileNotFoundError(msg)

    def build_part(self, json_file: Path) -> list[dict]:
        """Build a part using FreeCAD.

        Args:
            json_file: Path to the part JSON file.

        Returns:
            List of generated file information dictionaries.
        """
        json_path = Path(json_file).expanduser().resolve().absolute()
        data = self.load_json(json_path)
        name = data.get("name", json_path.stem)
        base_path = json_path.parent.parent  # Go up to parent directory

        # Check if features exist
        if not data.get("features"):
            logging.warning(f"No features found in part JSON: {json_path}")
            return []

        # Get FreeCAD binary
        try:
            freecad_app = self.get_freecad_app(base_path)
        except FileNotFoundError as e:
            logging.error(str(e))
            return []

        # Get the FreeCAD part script
        freecad_script = Path(__file__).resolve().parent / "cycax_part_freecad.py"

        if not freecad_script.exists():
            logging.error(f"FreeCAD part script not found: {freecad_script}")
            return []

        # Prepare environment variables
        environment = dict(os.environ)
        out_formats = self.config.get("out_formats", "STL,PNG")
        environment.update(
            {
                "CYCAX_JSON": str(json_path),
                "CYCAX_CWD": str(base_path),
                "CYCAX_OUT_FORMATS": out_formats,
                "CYCAX_MODE": "SINGLE",
            }
        )

        # Execute FreeCAD
        logging.info(f"Building FreeCAD part: {name}")
        result = subprocess.run(
            [str(freecad_app), str(freecad_script)],
            capture_output=True,
            text=True,
            env=environment,
            shell=False,
            check=False,
        )

        if result.stdout:
            logging.info(f"FreeCAD: {result.stdout}")
        if result.stderr:
            logging.error(f"FreeCAD: {result.stderr}")

        if result.returncode != 0:
            logging.error(f"FreeCAD build failed with return code: {result.returncode}")

        # Collect generated files
        part_dir = json_path.parent
        files = [
            {"file": part_dir / f"{name}-freecad.stl"},
            {"file": part_dir / f"{name}-perspectiveAll.png"},
            {"file": part_dir / f"{name}-perspective.dxf", "side": TOP},
            {"file": part_dir / f"{name}-perspectiveTop.png", "side": TOP},
            {"file": part_dir / f"{name}-freecad.FCStd", "description": "FreeCAD primary source file."},
            {"file": part_dir / f"{name}-freecad.step"},
        ]

        return self.file_list(files, self.engine_name, score=5)

    def build_assembly(self, json_file: Path) -> list[dict]:
        """Build an assembly using FreeCAD.

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

        # Get FreeCAD binary
        try:
            freecad_app = self.get_freecad_app(base_path)
        except FileNotFoundError as e:
            logging.error(str(e))
            return []

        # Get the FreeCAD assembly script
        freecad_script = Path(__file__).resolve().parent / "cycax_assembly_freecad.py"

        if not freecad_script.exists():
            logging.error(f"FreeCAD assembly script not found: {freecad_script}")
            return []

        # Prepare environment variables
        environment = dict(os.environ)
        out_formats = self.config.get("out_formats", "STL,PNG")
        environment.update(
            {
                "CYCAX_JSON": str(json_path),
                "CYCAX_CWD": str(base_path),
                "CYCAX_OUT_FORMATS": out_formats,
            }
        )

        # Execute FreeCAD
        logging.info(f"Building FreeCAD assembly: {name}")
        result = subprocess.run(
            [str(freecad_app), str(freecad_script)],
            capture_output=True,
            text=True,
            env=environment,
            shell=False,
            check=False,
        )

        if result.stdout:
            logging.info(f"FreeCAD: {result.stdout}")
        if result.stderr:
            logging.error(f"FreeCAD: {result.stderr}")

        if result.returncode != 0:
            logging.error(f"FreeCAD assembly build failed with return code: {result.returncode}")

        # Collect generated files
        assembly_dir = json_path.parent
        files = [
            {"file": assembly_dir / f"{name}-assembly.stl"},
            {"file": assembly_dir / f"{name}-assembly-ALL.png"},
            {"file": assembly_dir / f"{name}-assembly.FCStd", "description": "FreeCAD assembly source file."},
            {"file": assembly_dir / f"{name}-assembly.step"},
        ]

        return self.file_list(files, self.engine_name, score=5)
