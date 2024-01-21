import copy
import json
import logging
from collections import defaultdict
from pathlib import Path

from cycax.cycad.assembly_blender import AssemblyBlender
from cycax.cycad.assembly_openscad import AssemblyOpenSCAD
from cycax.cycad.cycad_part import CycadPart
from cycax.cycad.cycad_side import CycadSide
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


class AssemblyEngine:
    # TODO: Move to own file to avoid circular dependency
    # TODO: Make this an ABC.
    # TODO: Update assembly_blender and assembly_scad to inherit from here.

    def __init__(self, name: str, config: dict | None = None) -> None:
        self.name = name
        self._base_path = Path(".")
        self._config = {} if config is None else config
    
    def add(self, part_operation: dict):
        """Add the part to the assembly."""
        pass

    def build(self, path: Path | None = None):
        """Create the assembly of the parts added."""
        pass


class Assembly:
    """
    This Assembly class will take multiple different cycad parts and combine them together to form complex parts.

    Attributes:
        name: this is the destinct part number that the complex part will have.
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
        elif engine.lower() == "blender":
            assembler = AssemblyBlender(self.name)
        else:
            msg = f"""Engine {assembler} is not one of the recognized engines for assebling parts.
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

        for part in self.parts.values():
            data_files = part.render(engine=part_engine, engine_config=part_engine_config)
            self._part_files[part.part_no] = data_files

        data = self.export()
        for action in data["parts"]:
            assembler.add(action)
        assembler.build(self._base_path)

    def save(self, path: Path | None = None):
        """Save the assembly and added part to JSON files.

        Args:
            path: The location where the assembly is stored.
                A directory for each part will be created in this path.
        """

        if path is None:
            path = self._base_path
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

    def add(self, part: CycadPart, suggested_name: str = None) -> str:
        """This adds a part into the assembly.

        Once the part has been added to the assembler it can no longer be moved around or eddited.

        Args:
            part: this in the part that will be added to the assembly.
            suggested_name: A proposal for a part name, if a part with such a name exists then a name will be generated.

        Returns:
            The name of the part.
        """

        part.assembly = self
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
        """Get all the part of a type, same part_no.

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
        """This method will hold the front and the left while holding the top where it currently is.

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
            partside1:The CycadSide to be moved to match the plain of the other part.
            partside2: The CycadSide used as reference when moving part1.
        Raises:
            ValueError: if the side present in CycadSide does not match one of the expected side.
        """
        part1 = partside1._parent
        part2 = partside2._parent
        side1 = partside1.name
        side2 = partside2.name
        part2.make_bounding_box()
        part1.make_bounding_box()
        to_here = part2.bounding_box[side2]

        if side1 == BOTTOM:
            part1.at(z=to_here)
        elif side1 == TOP:
            z_size = part1.z_max - part1.z_min
            part1.at(z=to_here - z_size)
        elif side1 == LEFT:
            part1.at(x=to_here)
        elif side1 == RIGHT:
            x_size = part1.x_max - part1.x_min
            part1.at(x=to_here - x_size)
        elif side1 == FRONT:
            part1.at(y=to_here)
        elif side1 == BACK:
            y_size = part1.y_max - part1.y_min
            part1.at(y=to_here - y_size)
        else:
            msg = f"Side: {side1} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
            raise ValueError(msg)

        part1.make_bounding_box()

    def _final_place_(self, part):
        """
        It is used to move the move_holes to their final location before they are subtracted from
        the other part.
        """
        out_holes = []
        for hole in part.move_holes:
            temp_hole = copy.deepcopy(hole)
            rotation = [part.x_size, part.y_size, part.z_size]
            for rot in part.rotation:
                if rot["axis"] == "x":
                    rotation = temp_hole.swap_yz(rot=1, rotmax=rotation)
                elif rot["axis"] == "y":
                    rotation = temp_hole.swap_xz(rot=1, rotmax=rotation)
                elif rot["axis"] == "z":
                    rotation = temp_hole.swap_xy(rot=1, rotmax=rotation)
            if part.position[0] != 0:
                temp_hole.move(x=part.position[0])
            if part.position[1] != 0:
                temp_hole.move(y=part.position[1])
            if part.position[2] != 0:
                temp_hole.move(z=part.position[2])
            out_holes.append(temp_hole)
        return out_holes

    def subtract(self, partside1: CycadSide, part2: CycadPart):
        """
        This method adds the hols of part2 to the part1 on the side where they touch.
        This method will be used for moving around concube and harddive screw holes.

        Args:
            partside1: This is the part side that will receive the holes.
            part2: This is the part while will be used as the template when transferring holes.

        Raises:
            ValueError: if the side present in CycadSide does not match one of the expected side.
        """
        part1 = partside1._parent
        side = partside1.name

        holes = self._final_place_(part2)

        for hole in holes:
            if side == TOP:
                if hole.z == part1.bounding_box[TOP]:
                    hole.side = TOP
                    part1.insert_hole(hole)
            elif side == BOTTOM:
                if hole.z == part1.bounding_box[BOTTOM]:
                    hole.side = BOTTOM
                    part1.insert_hole(hole)
            elif side == LEFT:
                if hole.x == part1.bounding_box[LEFT]:
                    hole.side = LEFT
                    part1.insert_hole(hole)
            elif side == RIGHT:
                if hole.x == part1.bounding_box[RIGHT]:
                    hole.side = RIGHT
                    part1.insert_hole(hole)
            elif side == FRONT:
                if hole.y == part1.bounding_box[FRONT]:
                    hole.side = FRONT
                    part1.insert_hole(hole)
            elif side == BACK:
                if hole.y == part1.bounding_box[BACK]:
                    hole.side = BACK
                    part1.insert_hole(hole)
            else:
                msg = f"Side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
                raise ValueError(msg)
