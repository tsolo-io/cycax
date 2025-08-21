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
