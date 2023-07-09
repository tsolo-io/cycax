# Functions shared between the OpenSCAD based AssemblyEngine and PartEngine


class CycadOpenSCADEncoder:
    """Creates SCAD code from called methods."""

    head_lines = []
    tail_lines = []

    def text_out(self) -> str:
        code = ""
        for line in self.lines_out:
            code += line + "\n"
        return code

    def lines_out(self):
        yield from self.head_lines
        # This simple head/tail is only good for a single code block.
        # for line in self.tail_lines.reverse():
        #     yield line

    def difference(self):
        self.head_lines.append("difference(){")
        self.tail_lines.append("};")

    def translate(self, x: float, y: float, z: float) -> str:
        """
        This will move the object.

        Args:
            x: X position.
            y: Y position.
            z: Z position.
        """
        self.head_lines.append(f"translate([{x}, {y}, {z}]){{")
        self.tail_lines.append("};")
