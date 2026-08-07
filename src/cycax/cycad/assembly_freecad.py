# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import subprocess
from pathlib import Path

import orjson

from cycax.cycad.engines.base_assembly_engine import AssemblyEngine


class AssemblyFreeCAD(AssemblyEngine):
    """Assemble the parts into a FreeCAD model.

    Attributes:
        name: The part number of the complex part that is being assembled.
        config: Configuration for the FreeCAD assembly engine.
    """

    def __init__(self, name: str, config: dict | None = None) -> None:
        self.name = name
        self._base_path = Path(".")
        self._config = {} if config is None else config
        self._parts = []

    def add(self, part_operation: dict):
        """Add a part to the assembly.

        Args:
            part_operation: Dictionary containing part information:
                - part_no: Part identifier
                - position: [x, y, z] position
                - rotate: List of rotation operations
                - rotmax: [x_size, y_size, z_size] dimensions
                - colour: Part color
                - hash: Part hash
        """
        self._parts.append(part_operation)

    def get_freecad_app(self) -> Path:
        """Get the FreeCAD application binary path.

        Returns:
            Path to FreeCAD binary.

        Raises:
            FileNotFoundError: If FreeCAD binary cannot be found.
        """
        # Check if specified in config
        if self._config.get("freecad_app"):
            app_path = Path(self._config["freecad_app"])
            if app_path.exists():
                return app_path

        # Search common locations for AppImage
        search_paths = [
            Path("~/Applications").expanduser(),
            Path.home() / "Applications",
            self._base_path,
        ]

        for search_path in search_paths:
            if search_path.exists():
                for appimg in search_path.glob("FreeCAD*.AppImage"):
                    logging.info(f"Found FreeCAD AppImage: {appimg}")
                    return appimg

        msg = "FreeCAD binary not found. Please specify 'freecad_app' in config or install FreeCAD AppImage."
        raise FileNotFoundError(msg)

    def build(self, path: Path | None = None):
        """Create the assembly from the added parts.

        Args:
            path: The path where the assembly will be stored.

        Raises:
            ValueError: If no parts have been added.
            FileNotFoundError: If FreeCAD binary cannot be found.
        """
        if path is not None:
            self._base_path = path

        if not self._parts:
            msg = "No parts added to the assembly. Please call add() to add parts."
            raise ValueError(msg)

        # Create assembly JSON data
        assembly_data = {"name": self.name, "parts": self._parts}

        # Write assembly JSON to file
        assembly_json_file = self._base_path / f"{self.name}.json"
        assembly_json_file.write_text(orjson.dumps(assembly_data).decode("utf-8"))
        logging.info(f"Created assembly JSON: {assembly_json_file}")

        # Get FreeCAD binary
        try:
            freecad_app = self.get_freecad_app()
        except FileNotFoundError as e:
            logging.error(str(e))
            return

        # Get the FreeCAD assembly script
        freecad_script = Path(__file__).resolve().parent / "engines" / "cycax_assembly_freecad.py"

        if not freecad_script.exists():
            logging.error(f"FreeCAD assembly script not found: {freecad_script}")
            return

        # Prepare environment variables
        environment = dict(os.environ)
        environment.update(
            {
                "CYCAX_JSON": str(assembly_json_file),
                "CYCAX_CWD": str(self._base_path),
                "CYCAX_OUT_FORMATS": self._config.get("out_formats", "STL,PNG"),
            }
        )

        # Execute FreeCAD
        logging.info(f"Running FreeCAD assembly with: {freecad_app}")
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

        if result.returncode == 0:
            logging.info(f"Successfully created FreeCAD assembly: {self.name}")
        else:
            logging.error(f"FreeCAD assembly failed with return code: {result.returncode}")
