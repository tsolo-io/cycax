from cycax.cycad.assembly import Assembly
from cycax.cycad.location import TOP, BOTTOM, LEFT, RIGHT, BACK, FRONT, SIDES
from pathlib import Path
class ComplexAssembly:
    """
    This class will allow for an assembly to be formed from another assembly.
    """

    def __init__(self, name: str):
        self.name = name.strip().replace("-", "_").lower()
        self.assemblies = []
        self._base_path = Path(".")

        ####
        # self._part_files = defaultdict(list)
        ####

    def add(self, assembly: Assembly):
        """
        Adds a new Assembly into the list of Assemblies.
        """
        self.assemblies.append(assembly)

    def level(self, assembly1: Assembly, assembly1_side: str, assembly2: Assembly, assembly2_side: str):
        """
        Align the two sides onto the same plain.

        Moves assembly1 so that its given side is on the same plain as the given
        side of assembly2. e.g. `level(assembly1.front assembly2.back)` will move assembly1
        so that its front is on the same plain as the back of assembly2.

        Args:
            assembly1: The Assembly to be moved to match the plain of the other assembly.
            assembly2: The Assembly used as reference when moving assembly1.
        Raises:
            ValueError: When the side present in Assembly does not match one of the expected sides.
        """
        if assembly1_side not in SIDES or assembly2_side not in SIDES:
            msg = f"Side: {assembly1_side} or Side: {assembly2_side} is not one of {SIDES}"
            raise ValueError(msg)
        
        assembly1_bounding_box = assembly1.bounding_box
        assembly2_bounding_box = assembly2.bounding_box
        to_here = assembly2_bounding_box[assembly2_side]

        if assembly1_side == BOTTOM:
            assembly1.at(z=to_here)
        elif assembly1_side == TOP:
            z_size = assembly1_bounding_box[TOP] - assembly1_bounding_box[BOTTOM]
            assembly1.at(z=to_here - z_size)
        elif assembly1_side == LEFT:
            assembly1.at(x=to_here)
        elif assembly1_side == RIGHT:
            x_size = assembly1_bounding_box[RIGHT] - assembly1_bounding_box[LEFT]
            assembly1.at(x=to_here - x_size)
        elif assembly1_side == FRONT:
            assembly1.at(y=to_here)
        elif assembly1_side == BACK:
            y_size = assembly1_bounding_box[BACK] - assembly1_bounding_box[FRONT]
            assembly1.at(y=to_here - y_size)
        else:
            msg = f"Side: {assembly1_side} is not one of {SIDES}."
            raise ValueError(msg)

    def subtract(self, assembly1: Assembly, assembly1_side: str, assembly2: Assembly):
        """
        Loops through the parts in each assemly and adds the features from assembly2 that touch the face of assembly1.

        Args:
            assembly1: The assembly that you add the features to.
            assembly1_side: The side of the assembly that you add features to.
            assembly2: The assemly that is used as the template when transferring features.
        """
        for part1 in assembly1.parts.values():
            if assembly1_side==TOP:
                for part2 in assembly2.parts.values():
                    part1.top.subtract(part2=part2)
            elif assembly1_side==BOTTOM:
                for part2 in assembly2.parts.values():
                    part1.bottom.subtract(part2=part2)
            elif assembly1_side==LEFT:
                for part2 in assembly2.parts.values():
                    part1.left.subtract(part2=part2)
            elif assembly1_side==RIGHT:
                for part2 in assembly2.parts.values():
                    part1.right.subtract(part2=part2)
            elif assembly1_side==FRONT:
                for part2 in assembly2.parts.values():
                    part1.front.subtract(part2=part2)
            elif assembly1_side==BACK:
                for part2 in assembly2.parts.values():
                    part1.back.subtract(part2=part2)
            else:
                msg = f"{assembly1_side} not in {SIDES}."
                raise ValueError(msg)

    def combine_assemblies(self) -> Assembly:
        """
        Combine all the assemblies into one Assembly.

        Returns:
            Combined Assembly formed from all the assemblies in the list of Assemblies.
        """
        total_parts = {}
        for assembly in self.assemblies:
            total_parts.update(assembly.parts)
        assembly_out = Assembly(name=self.name)
        assembly_out.parts = total_parts
        assembly_out._base_path = self._base_path
        return assembly_out
