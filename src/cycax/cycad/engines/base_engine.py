# SPDX-FileCopyrightText: 2025, 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from pathlib import Path


class Engine:
    """Base class for unified engines that can build both parts and assemblies.

    Unlike separate PartEngine and AssemblyEngine classes, this unified Engine
    can process JSON files containing either part definitions (with "features")
    or assembly definitions (with "parts") and build them accordingly.

    Attributes:
        config: Engine-specific configuration dictionary.
    """

    def __init__(self, config: dict | None = None):
        """Initialize the engine.

        Args:
            config: Optional configuration dictionary for the engine.
        """
        self.config = dict(config or {})

    def is_part(self, data: dict) -> bool:
        """Determine if JSON data represents a part.

        Args:
            data: Parsed JSON data.

        Returns:
            True if data represents a part (has "features"), False otherwise.
        """
        return "features" in data

    def is_assembly(self, data: dict) -> bool:
        """Determine if JSON data represents an assembly.

        Args:
            data: Parsed JSON data.

        Returns:
            True if data represents an assembly (has "parts"), False otherwise.
        """
        return "parts" in data

    def load_json(self, json_file: Path) -> dict:
        """Load and parse a JSON file.

        Args:
            json_file: Path to the JSON file.

        Returns:
            Parsed JSON data as a dictionary.

        Raises:
            FileNotFoundError: If the JSON file doesn't exist.
        """
        json_path = Path(json_file).expanduser().resolve().absolute()
        if not json_path.exists():
            msg = f"JSON file not found: {json_path}"
            raise FileNotFoundError(msg)

        data = json.loads(json_path.read_text())
        return data

    def build_part(self, json_file: Path) -> list[dict]:
        """Build a part from its JSON definition.

        This method should be implemented by subclasses to handle
        part-specific building logic.

        Args:
            json_file: Path to the part JSON file.

        Returns:
            List of generated file information dictionaries.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        msg = "build_part must be implemented by subclass"
        raise NotImplementedError(msg)

    def build_assembly(self, json_file: Path) -> list[dict]:
        """Build an assembly from its JSON definition.

        This method should be implemented by subclasses to handle
        assembly-specific building logic.

        Args:
            json_file: Path to the assembly JSON file.

        Returns:
            List of generated file information dictionaries.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        msg = "build_assembly must be implemented by subclass"
        raise NotImplementedError(msg)

    def build_bulk(self, json_files: list[Path] | Path) -> list[dict]:
        """Build parts and assemblies from a list of JSON files.

        This method processes JSON files in order, automatically detecting
        whether each file represents a part or an assembly and building
        accordingly. Artifacts are placed in the same directory as the
        JSON file.

        Args:
            json_files: Single Path or list of Paths to JSON files to build.

        Returns:
            List of all generated file information dictionaries.
        """
        if isinstance(json_files, Path):
            json_files = [json_files]

        all_artifacts = []

        for json_file in json_files:
            json_path = Path(json_file).expanduser().resolve().absolute()
            logging.info(f"Processing: {json_path}")

            try:
                data = self.load_json(json_path)

                if self.is_part(data):
                    logging.info(f"Building part: {data.get('name', 'unknown')}")
                    artifacts = self.build_part(json_path)
                elif self.is_assembly(data):
                    logging.info(f"Building assembly: {data.get('name', 'unknown')}")
                    artifacts = self.build_assembly(json_path)
                else:
                    logging.warning(f"Unknown JSON type (no 'features' or 'parts'): {json_path}")
                    continue

                all_artifacts.extend(artifacts)

            except Exception as error:
                logging.error(f"Error processing {json_path}: {error}")
                continue

        return all_artifacts

    def file_list(self, files: list[dict], engine_name: str, score: int = 5) -> list[dict]:
        """Generate a standardized list of artifact files.

        Args:
            files: List of file dictionaries with 'file' key (Path).
            engine_name: Name of the engine that generated the files.
            score: Priority score for the files (higher is better).

        Returns:
            List of file information dictionaries with metadata.
        """
        artifact_files = []
        for file_info in files:
            filepath = file_info["file"]
            if filepath.exists():
                file_info["type"] = filepath.suffix.strip(".").upper()
                file_info["engine"] = engine_name
                file_info["score"] = score
                artifact_files.append(file_info)
            else:
                logging.warning(f"File does not exist: {filepath}")

        return artifact_files
