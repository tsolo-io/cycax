# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import logging
import os
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from cycax.cycad.assembly_openscad import AssemblyOpenSCAD
from cycax.cycad.cycad_part import CycadPart
from cycax.cycad.cycad_side import CycadSide
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

    def save(self, path: Path | str | None = None):
        """Save the assembly and added part to JSON files.

        Args:
            path: The location where the assembly is stored.
                A directory for each part will be created in this path.
        """

        if path is None:
            path = self._base_path
        path = Path(path)
        path.mkdir(parents=False, exist_ok=True)
        if not path.exists():
            msg = f"The directory {path} does not exists."
            raise FileNotFoundError(msg)

        for item in self.parts.values():
            item.save(path)

        self._base_path = path
        data = self.export()
        data_filename = path / f"{self.name}.json"
        data_filename.write_text(json.dumps(data))

    def merge(self, part1: CycadPart, part2: CycadPart):
        """This method will be used to merge 2 parts together
        which have identical sizes but different features.

        Args:
            part1: this part will receive the features present on part2.
            part2: this part will receive the features present on part1.

        Raises:
            ValueError: if the sizes of the parts are not identical.
        """
        if part1.x_size == part2.x_size and part1.y_size == part2.y_size and part1.z_size == part2.z_size:
            for item in part2.features:
                if item not in part1.features:
                    part1.features.append(item)
            for item in part2.move_holes:
                if item not in part1.move_holes:
                    part1.move_holes.append(item)
            part2.features = part1.features
            part2.move_holes = part1.move_holes
        else:
            msg = f"merging {part1} and {part2} but they are not of the same size."
            raise ValueError(msg)

    def add(self, part: CycadPart, suggested_name: str | None = None) -> str:
        """This adds a part into the assembly.

        Once the part has been added to the assembler it can no longer be edited.

        Args:
            part: this in the part that will be added to the assembly.
            suggested_name: A proposal for a part name, if a part with such a name exists then a name will be generated.

        Returns:
            The name of the part.
        """

        part.assembly = self
        part._base_path = self._base_path
        part_name = part.get_name(suggested_name)
        if part_name in self.parts:
            msg = f"Part with name/id {part_name} already in parts catalogue."
            raise KeyError(msg)
        self.parts[part_name] = part
        return part_name

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

    def rotate_freeze_top(self, part: CycadPart):
        """This method will rotate the front and the left while holding the top where it currently is.

        Args:
            part: This is the part that will be rotated.
        """
        part.rotation.append({"axis": "z", "angle": 90})
        part.x_max, part.y_max = part.y_max, part.x_max
        part.x_min, part.y_min = part.y_min, part.x_min
        part.make_bounding_box()

    def rotate_freeze_left(self, part: CycadPart):
        """This method will rotate the top and front while holding the left where it currently is.

        Args:
            part: This is the part that will be rotated.
        """
        part.rotation.append({"axis": "x", "angle": 90})
        part.y_max, part.z_max = part.z_max, part.y_max
        part.y_min, part.z_min = part.z_min, part.y_min
        part.make_bounding_box()

    def rotate_freeze_front(self, part: CycadPart):
        """This method will rotate the left and top while holding the front where it currently is.

        Args:
            part: This is the part that will be rotated.
        """
        part.rotation.append({"axis": "y", "angle": 90})
        part.x_max, part.z_max = part.z_max, part.x_max
        part.x_min, part.z_min = part.z_min, part.x_min
        part.make_bounding_box()

    def level(self, partside1: CycadSide, partside2: CycadSide):
        """
        Alight the two sides onto the same plain.

        Moves part1 so that its given side is on the same plain as the given
        side of parts2. e.g. `level(part1.front part2.back)` will move part1
        so that its front is on the same plain as the back of part2.

        Args:
            partside1: The CycadSide to be moved to match the plain of the other part.
            partside2: The CycadSide used as reference when moving part1.
        Raises:
            ValueError: When the side present in CycadSide does not match one of the expected sides.
        """
        part1 = partside1._parent
        part2 = partside2._parent
        part1side = partside1.name
        part2side = partside2.name
        part2.make_bounding_box()
        part1.make_bounding_box()
        to_here = part2.bounding_box[part2side]

        if part1side == BOTTOM:
            part1.at(z=to_here)
        elif part1side == TOP:
            z_size = part1.z_max - part1.z_min
            part1.at(z=to_here - z_size)
        elif part1side == LEFT:
            part1.at(x=to_here)
        elif part1side == RIGHT:
            x_size = part1.x_max - part1.x_min
            part1.at(x=to_here - x_size)
        elif part1side == FRONT:
            part1.at(y=to_here)
        elif part1side == BACK:
            y_size = part1.y_max - part1.y_min
            part1.at(y=to_here - y_size)
        else:
            msg = f"Side: {part1side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
            raise ValueError(msg)

        part1.make_bounding_box()

    def _final_place(self, part: CycadPart):
        """
        It is used to move the move_holes to their final location before they are subtracted from
        the other part.
        """
        for feature in part.move_holes:
            temp_feature = copy.deepcopy(feature)
            rotation = [part.x_size, part.y_size, part.z_size]
            for rot in part.rotation:
                if rot["axis"] == "x":
                    rotation = temp_feature.swap_yz(rot=1, rotmax=rotation)
                elif rot["axis"] == "y":
                    rotation = temp_feature.swap_xz(rot=1, rotmax=rotation)
                elif rot["axis"] == "z":
                    rotation = temp_feature.swap_xy(rot=1, rotmax=rotation)
            if part.position[0] != 0:
                temp_feature.move(x=part.position[0])
            if part.position[1] != 0:
                temp_feature.move(y=part.position[1])
            if part.position[2] != 0:
                temp_feature.move(z=part.position[2])
            yield temp_feature

    def subtract(self, partside1: CycadSide, part2: CycadPart):
        """
        This method adds the features of part2 to the part1 on the side where they touch.
        This method will be used for moving around conn-cube and harddive screw holes.

        Args:
            partside1: The part side that will receive the features.
            part2: The part that is used as the template when transferring features.

        Raises:
            ValueError: When the side present in CycadSide does not match one of the expected sides.
        """
        part1 = partside1._parent
        side = partside1.name

        for feature in self._final_place(part2):
            if feature.name == "cube":
                if side == TOP:
                    if (feature.z - feature.z_size/2) == part1.bounding_box[TOP]:
                        feature.side = TOP
                        part1.insert_feature(feature)
                elif side == BOTTOM:
                    if (feature.z + feature.z_size/2) == part1.bounding_box[BOTTOM]:
                        feature.side = BOTTOM
                        part1.insert_feature(feature)
                elif side == LEFT:
                    if (feature.x + feature.x_size/2) == part1.bounding_box[LEFT]:
                        feature.side = LEFT
                        part1.insert_feature(feature)
                elif side == RIGHT:
                    if (feature.x - feature.x_size/2) == part1.bounding_box[RIGHT]:
                        feature.side = RIGHT
                        part1.insert_feature(feature)
                elif side == FRONT:
                    if (feature.y + feature.y_size/2) == part1.bounding_box[FRONT]:
                        feature.side = FRONT
                        part1.insert_feature(feature)
                elif side == BACK:
                    if (feature.y - feature.y_size/2) == part1.bounding_box[BACK]:
                        feature.side = BACK
                        part1.insert_feature(feature)
                else:
                    msg = f"Side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
                    raise ValueError(msg)
            else:
                if side == TOP:
                    if feature.z == part1.bounding_box[TOP]:
                        feature.side = TOP
                        part1.insert_feature(feature)
                elif side == BOTTOM:
                    if feature.z == part1.bounding_box[BOTTOM]:
                        feature.side = BOTTOM
                        part1.insert_feature(feature)
                elif side == LEFT:
                    if feature.x == part1.bounding_box[LEFT]:
                        feature.side = LEFT
                        part1.insert_feature(feature)
                elif side == RIGHT:
                    if feature.x == part1.bounding_box[RIGHT]:
                        feature.side = RIGHT
                        part1.insert_feature(feature)
                elif side == FRONT:
                    if feature.y == part1.bounding_box[FRONT]:
                        feature.side = FRONT
                        part1.insert_feature(feature)
                elif side == BACK:
                    if feature.y == part1.bounding_box[BACK]:
                        feature.side = BACK
                        part1.insert_feature(feature)
                else:
                    msg = f"Side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
                    raise ValueError(msg)
