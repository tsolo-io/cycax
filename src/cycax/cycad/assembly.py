# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
from collections import defaultdict, namedtuple
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from cycax.cycad.assembly_openscad import AssemblyOpenSCAD
from cycax.cycad.assembly_side import (
    AssemblySide,
    AssemblySideBack,
    AssemblySideBottom,
    AssemblySideFront,
    AssemblySideLeft,
    AssemblySideRight,
    AssemblySideTop,
)
from cycax.cycad.cycad_part import CycadPart
from cycax.cycad.engines.base_assembly_engine import AssemblyEngine
from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class Assembly:
    """
    The Assembly takes multiple CYCAD parts and combine them together to form a complex part.

    Attributes:
        name: The part number of the assembly.
    """

    def __init__(self, name: str):
        self.name = name.strip().replace("-", "_").lower()
        self.parts = {}
        self._base_path = Path(".")
        self._part_files = defaultdict(list)
        self.external_features = []
        self.left = AssemblySideLeft(self)
        self.right = AssemblySideRight(self)
        self.top = AssemblySideTop(self)
        self.bottom = AssemblySideBottom(self)
        self.front = AssemblySideFront(self)
        self.back = AssemblySideBack(self)
        self.assemblies = []

    def _get_assembler(self, engine: str = "OpenSCAD", engine_config: dict | None = None) -> AssemblyEngine:
        logging.info("Calling to the assembler")
        if engine.lower() == "openscad":
            assembler = AssemblyOpenSCAD(self.name, config=engine_config)
        else:
            msg = f"""Engine {engine} is not one of the recognized engines for assebling parts.
                Choose one of OpenSCAD (default) or Blender."""
            raise ValueError(msg)
        return assembler

    def render(
        self,
        engine: str = "OpenSCAD",
        engine_config: dict | None = None,
        part_engine: str = "OpenSCAD",
        part_engine_config: dict | None = None,
    ):
        """Run the assembly and produce output files.

        Args:
            engine: The type of engine to use for assembly.
            engine_config: Additional config to pass to the engine used for assembly.
            part_engine: The engine to use for part creation.
            part_engine_config: Additional config to pass to the part engine.
        """
        assembler = self._get_assembler(engine, engine_config)
        assembler._base_path = self._base_path  # HACK

        for part in self.parts.values():
            data_files = part.render(engine=part_engine, engine_config=part_engine_config)
            self._part_files[part.part_no] = data_files

        self.build(engine=assembler, part_engines=[])

    def build(self, engine: AssemblyEngine | None = None, part_engines: list[PartEngine] | None = None):
        """Create the parts defined in the assembly and assemble.

        Args:
            engine: Instance of AssemblyEngine to use.
            part_engines: Instances of PartEngine to use on parts.
        """

        if engine is not None:
            engine.set_name(self.name)
            engine.set_path(self._base_path)
        else:
            logging.warning("No assembly engine specified. No assembly output.")

        if part_engines is not None:
            unique_parts = {}
            # Create the Parts.
            for part in self.parts.values():
                if part.part_no not in unique_parts:
                    unique_parts[part.part_no] = part
                    for part_engine in part_engines:
                        part_engine.create(part)
                else:
                    logging.warning("The part %s is already processed", part.part_no)

            # For asyncrounouse build environments, e.g. CyCAx Server and LinkLocation
            # Creation on the Part in the Engine will start the build in the background.
            # The build step is a collect/download step.
            # Build the parts.
            for part in unique_parts.values():
                for part_engine in part_engines:
                    part_engine.new(part.part_no, self._base_path)
                    part_engine.config["out_formats"] = [("png", "ALL"), ("STL",), ("DXF", TOP)]
                    data_files = part.build(engine=part_engine)
                    self._part_files[part.part_no] = data_files
        else:
            logging.warning("No Part engines given. No Parts created.")

        if engine is not None:
            data = self.export()
            for action in data["parts"]:
                engine.add(action)
            engine.build()

    def _run_build_in_parallel(self, part_engine: PartEngine, part: dict, worker_path: Path) -> dict:
        logging.info("Enter Building part %s in parallel: pid %s", part.part_no, os.getpid())
        part_engine.new(part.part_no, worker_path)
        part_engine.config["out_formats"] = [("png", "ALL"), ("STL",), ("DXF", TOP)]
        data_files = part_engine.build(part)
        logging.info("Exit Part %s built in parallel: pid %s", part.part_no, os.getpid())
        return {"part_no": part.part_no, "data_files": data_files}

    def build_in_parallel(self, engine: AssemblyEngine | None = None, part_engines: list[PartEngine] | None = None):
        """Create the parts defined in the assembly and assemble.

        Args:
            engine: Instance of AssemblyEngine to use.
            part_engines: Instances of PartEngine to use on parts.
        """

        if engine:
            engine.set_name(self.name)
            engine.set_path(self._base_path)
        else:
            logging.warning("No assembly engine specified. No assembly output.")

        if part_engines is not None:
            unique_parts = {}
            # Create the Parts.
            for part in self.parts.values():
                if part.part_no not in unique_parts:
                    unique_parts[part.part_no] = part
                else:
                    logging.warning("The part %s is already processed", part.part_no)

            # For asyncrounouse build environments, e.g. CyCAx Server and LinkLocation
            # Creation on the Part in the Engine will start the build in the background.
            # The build step is a collect/download step.
            # Build the parts.
            results = []
            with ProcessPoolExecutor() as executor:
                for part in unique_parts.values():
                    for part_engine in part_engines:
                        results.append(executor.submit(self._run_build_in_parallel, part_engine, part, self._base_path))

                for result in results:
                    try:
                        data_files = result.result()
                        if data_files:
                            if data_files.get("part_no") in self._part_files:
                                self._part_files[data_files.get("part_no")].extend(data_files.get("data_files"))
                            else:
                                self._part_files[data_files.get("part_no")] = data_files.get("data_files")
                    except Exception as error:
                        logging.error("Error building part %s", error)
        else:
            logging.warning("No Part engines given. No Parts created.")

        if engine:
            data = self.export()
            for action in data["parts"]:
                engine.add(action)
            engine.build()

    def save(self, path: Path | str | None = None) -> list[Path]:
        """Save the assembly and parts to JSON files.

        Args:
            path: The location where the assembly is stored.
                A directory for each part will be created in this path.
        """

        if path is None:
            path = self._base_path
        self._base_path = path
        path = Path(path)
        path.mkdir(parents=False, exist_ok=True)
        if not path.exists():
            msg = f"The directory {path} does not exists."
            raise FileNotFoundError(msg)
        # Save the parts
        for item in self.parts.values():
            item.save(path)

        # Save the assembly
        data = self.export()
        data_filename = path / f"{self.name}.json"
        data_filename = data_filename.expanduser().resolve().absolute()
        data_filename.write_text(json.dumps(data))
        logging.info("Saved assembly '%s' to %s", self.name, data_filename)

        return data_filename

    @property
    def bounding_box(self) -> dict:
        """
        Creates a bounding box that will give the plane of each side of the assembly.

        Returns:
            Bounding box.
        """
        x_min = None
        x_max = None
        y_min = None
        y_max = None
        z_min = None
        z_max = None
        for part in self.parts.values():
            x_min = self._min(x_min, part.x_min)
            y_min = self._min(y_min, part.y_min)
            z_min = self._min(z_min, part.z_min)
            x_max = self._max(x_max, part.x_max)
            y_max = self._max(y_max, part.y_max)
            z_max = self._max(z_max, part.z_max)
        bounding_box = {LEFT: x_min, FRONT: y_min, BOTTOM: z_min, RIGHT: x_max, BACK: y_max, TOP: z_max}
        return bounding_box

    def _min(self, current_value: float, new_value: float):
        if current_value is None:
            return new_value
        else:
            return min(current_value, new_value)

    def _max(self, current_value: float, new_value: float):
        if current_value is None:
            return new_value
        else:
            return max(current_value, new_value)

    @property
    def center(self) -> tuple[float, float, float]:
        """
        return the center of the assembly.

        Returns:
            The coordinates of the center of the assembly.
        """
        center_x = 0
        center_y = 0
        center_z = 0
        for part in self.parts.values():
            center_x = min(part.center[0], center_x)
            center_y = min(part.center[1], center_y)
            center_z = min(part.center[2], center_z)
        coordinate = namedtuple("Coordinate", ["x", "y", "z"])
        return coordinate(x=center_x, y=center_y, z=center_z)

    def move(self, x: float | None = None, y: float | None = None, z: float | None = None):
        """This method will be used for moving the assembly.

        Args:
            x: the amount the assembly should be moved by along the x axis.
            y: the amount the assembly should be moved by along the y axis.
            z: the amount the assembly should be moved by along the z axis
        """

        for part in self.parts.values():
            part.move(x=x, y=y, z=z)

    def at(
        self,
        min_x: float | None = None,
        min_y: float | None = None,
        min_z: float | None = None,
        center_x: float | None = None,
        center_y: float | None = None,
        center_z: float | None = None,
    ):
        """Place parts in the assembly at the exact provided coordinates.

        Args:
            min_x: New position of the assemblies closest point to the origin on the x-axis.
            min_y: New position of the assemblies closest point to the origin on the y-axis.
            min_z: New position of the assemblies closest point to the origin on the z-axis.
            center_x: New position of the assemblies center on the x-axis.
            center_y: New position of the assemblies center on the y-axis.
            center_z: New position of the assemblies center on the z-axis.
        """
        if min_x and center_x:
            msg = "Cannot specify both min_x and center_x"
            raise ValueError(msg)
        if min_y and center_y:
            msg = "Cannot specify both min_y and center_y"
            raise ValueError(msg)
        if min_z and center_z:
            msg = "Cannot specify both min_z and center_z"
            raise ValueError(msg)

        x_move, y_move, z_move = None, None, None

        if min_x is not None:
            x_move = min_x - self.bounding_box[LEFT]
        if min_y is not None:
            y_move = min_y - self.bounding_box[FRONT]
        if min_z is not None:
            z_move = min_z - self.bounding_box[BOTTOM]
        if center_x is not None:
            x_move = center_x - self.bounding_box[LEFT] / 2
        if center_y is not None:
            y_move = center_y - self.bounding_box[FRONT] / 2
        if center_z is not None:
            z_move = center_z - self.bounding_box[BOTTOM] / 2

        for part in self.parts.values():
            if x_move is not None:
                part.at(x=x_move + part.position[0])
            if y_move is not None:
                part.at(y=y_move + part.position[1])
            if z_move is not None:
                part.at(z=z_move + part.position[2])

    def add(self, part, suggested_name: str | None = None, *, external_subtract: bool = False):
        """This adds a part into the assembly.

        Once the part has been added to the assembler it can no longer be edited.

        Args:
            part: If this is a part it will add it to the list of parts, else it will add it to the list of assemblies.
            suggested_name: A proposal for a part name, if a part with such a name exists then a name will be generated.

        Returns:
            The name of the part if a part gets returned.
        """

        if isinstance(part, Assembly):
            self.assemblies.append(part)
        else:
            part.assembly = self
            part._base_path = self._base_path
            part_name = part.get_name(suggested_name)
            if part_name in self.parts:
                msg = f"Part with name/id {part_name} already in parts catalogue."
                raise KeyError(msg)
            self.parts[part_name] = part
            if external_subtract:
                self.external_features.append(part.external_features)
            return part_name

    def level(
        self,
        *,
        left: AssemblySide | None = None,
        right: AssemblySide | None = None,
        front: AssemblySide | None = None,
        back: AssemblySide | None = None,
        top: AssemblySide | None = None,
        bottom: AssemblySide | None = None,
    ):
        """
        A shorthand level method for assembly.

        This method can only be used if the Assembly was added to an Assembly.
        The method is to replace multiple calls to assembly.level and assembly.subtract for a part.

        Args:
            left: Side to lign the left side up with.
            right: Side to lign the right side up with
            front: Side to lign the front up with.
            back: Side to lign the back up with.
            top: Side to lign the top up with.
            bottom: Side to lign the bottom up with

        Raises:
            ValueError: When both left and right side is give.
            ValueError: When both front and back side is give.
            ValueError: When both top and bottom side is give.
            ValueError: When the part is not part of an assembly.
            ValueError: When leveling with the same part twice and subtracting.
        """
        level_with = {}
        if left is not None:
            if right is not None:
                msg = "Cannot level left and right at the same time."
                raise ValueError(msg)
            level_with["left"] = left
        elif right is not None:
            level_with["right"] = right

        if top is not None:
            if bottom is not None:
                msg = "Cannot level top and bottom at the same time."
                raise ValueError(msg)
            level_with["top"] = top
        elif bottom is not None:
            level_with["bottom"] = bottom

        if front is not None:
            if back is not None:
                msg = "Cannot level front and back at the same time."
                raise ValueError(msg)
            level_with["front"] = front
        elif back is not None:
            level_with["back"] = back

        for name, var in level_with.items():
            assembly_side = getattr(self, name)
            assembly_side.level(var)

    def get_part(self, name: str) -> CycadPart:
        """Get a part from the assembly based on part name.

        Args:
            name: The name or ID of a part.

        Returns:
            A matching part.

        Raises:
            KeyError: is raised when we cannot find the part with the given name.
        """
        return self.parts[name]

    def get_parts_by_no(self, part_no: str) -> list[CycadPart]:
        """Get all the parts of a type, same part_no.

        Args:
            part_no: The part_no of the parts we are looking for.

        Returns:
            The part with the given part_no.
        """
        parts = []
        for part in self.parts.values():
            if part.part_no == part_no:
                parts.append(part)
        return parts

    def export(self) -> dict:
        """This creates a dict of the assembly, used to make the JSON.

        Returns:
            This is the dict that will be used to form a JSON decoded in assembly.
        """
        list_out = []
        for item in self.parts.values():
            dict_part = {
                "part_no": item.part_no,
                "position": item.position,
                "rotate": item.rotation,
                "rotmax": [item.x_size, item.y_size, item.z_size],
                "colour": item.colour,
            }
            list_out.append(dict_part)
        dict_out = {}
        dict_out["name"] = self.name
        dict_out["parts"] = list_out
        return dict_out

    def rotate_freeze_top(self):
        """
        Rotate the front and the left while holding the top where it currently is. Of all the parts in an assembly.
        """
        back = self.bounding_box[BACK]
        for part in self.parts.values():
            x = part.position[0] + (part.x_max - part.x_min) / 2
            y = part.position[1] + (part.y_max - part.y_min) / 2
            x, y = back - y, x
            part.rotate_freeze_top()
            part.position[0] = x - (part.x_max - part.x_min) / 2
            part.position[1] = y - (part.y_max - part.y_min) / 2

    def rotate_freeze_left(self):
        """
        Rotate the top and front while holding the left where it currently is. Of all the parts in an assembly.
        """
        top = self.bounding_box[TOP]
        for part in self.parts.values():
            y = part.position[1] + (part.y_max - part.y_min) / 2
            z = part.position[2] + (part.z_max - part.z_min) / 2
            y, z = top - z, y
            part.rotate_freeze_left()
            part.position[1] = y - (part.y_max - part.y_min) / 2
            part.position[2] = z - (part.z_max - part.z_min) / 2

    def rotate_freeze_front(self):
        """
        Rotate the left and top while holding the front where it currently is. Of all the parts in an assembly.
        """
        right = self.bounding_box[RIGHT]
        for part in self.parts.values():
            x = part.position[0] + (part.x_max - part.x_min) / 2
            z = part.position[2] + (part.z_max - part.z_min) / 2
            x, z = z, right - x
            part.rotate_freeze_front()
            part.position[0] = x - (part.x_max - part.x_min) / 2
            part.position[2] = z - (part.z_max - part.z_min) / 2

    def rotate(self, actions: str):
        """Rotate the assembly several times.

        Example: `Assembly.rotate("xxyzyy")` is the same as two `rotate_freeze_front`, `rotate_freeze_left`,
        `rotate_freeze_top`, and two `rotate_freeze_left`.
        Where rotate_freeze_<side> results in one 90degrees counter clock wise rotations on the side.

        Args:
            actions: This is a string specifying rotations.

        Raises:
            ValueError: When the given actions contains a string that is non x, y, or z.
        """
        for action in actions:
            match action.lower():
                case "x":
                    self.rotate_freeze_left()
                case "y":
                    self.rotate_freeze_front()
                case "z":
                    self.rotate_freeze_top()
                case _:
                    msg = f"""The actions permissable by rotate are 'x', 'y' or 'z'.
                            {action} is not one of the permissable actions."""
                    raise ValueError(msg)

    def combine_all_assemblies(self, new_name: str | None = None, path: Path | None = None):
        """
        Combine all the assemblies into one Assembly.

        Returns:
            Combined Assembly formed from all the assemblies in the list of Assemblies.
        """
        total_parts = {}
        for n, assembly in enumerate(self.assemblies):
            for part_name, part in assembly.parts.items():
                total_parts[f"assembly_{n}_{part_name}"] = part
        total_parts.update(self.parts)
        if new_name:
            assembly_out = Assembly(name=new_name)
        else:
            assembly_out = Assembly(name=self.name)
        assembly_out.parts = total_parts
        if path:
            assembly_out._base_path = path
        else:
            assembly_out._base_path = self._base_path
        return assembly_out


def import_build(
    base_path: Path, data: dict, engine: AssemblyEngine | None = None, part_engines: list[PartEngine] | None = None
):
    """Create the parts defined in the assembly and assemble.

    Args:
        engine: Instance of AssemblyEngine to use.
        part_engines: Instances of PartEngine to use on parts.
    """

    if engine is None:
        logging.warning("No assembly engine specified. No assembly output.")
    else:
        engine.set_name(data.get("name"))
        engine.set_path(base_path)

    if part_engines is not None and "parts" in data:
        unique_parts = {}
        # Create the Parts.
        for part in data["parts"]:
            part_no = part.get("part_no")
            if part_no not in unique_parts:
                unique_parts[part_no] = part
                for part_engine in part_engines:
                    part_engine.create(part)
            else:
                logging.warning("The part %s is already processed", part_no)

        # For asyncrounouse build environments, e.g. CyCAx Server and LinkLocation
        # Creation on the Part in the Engine will start the build in the background.
        # The build step is a collect/download step.
        # Build the parts.
        for part in unique_parts.values():
            part_no = part.get("part_no")
            for part_engine in part_engines:
                part_engine.new(part_no, base_path)
                part_engine.config["out_formats"] = [("png", "ALL"), ("STL",), ("DXF", TOP)]
                part_json = base_path / part_no / f"{part_no}.json"
                data = json.loads(part_json.read_text())
                data_files = part_engine.import_build(data)
                # part_files[part_no] = data_files
    else:
        logging.warning("No Part engines given. No Parts created.")

    if engine is not None and "parts" in data:
        for action in data["parts"]:
            engine.add(action)
        engine.build()
