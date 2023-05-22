import json


class assembly_stl:
    def __init__(self, part_no: str) -> None:
        """initializes and stl assembler"""
        self.part_no = part_no

    def fetch_part(self, part: str):
        """Retrieves the part that will be imported and possitioned."""
        return 'import("../STL/' + part + '.stl");'

    def swapXY(self, rotation, rot: float, max: float):
        """Used to help rotate the object on the spot while freezing the top"""
        while rot != 0:
            rotation[0], rotation[1] = max - rotation[1], rotation[0]
            rot = rot - 1
        return rotation

    def swapXZ(self, rotation, rot: float, max: float):
        """Used to help rotate the object on the spot while freezing the front"""
        while rot != 0:
            rotation[0], rotation[2] = rotation[2], max - rotation[0]
            rot = rot - 1
        return rotation

    def swapYZ(self, rotation, rot: float, max: float):
        """Used to help rotate the object on the spot while freezing the left"""
        while rot != 0:
            rotation[1], rotation[2] = max - rotation[2], rotation[1]
            rot = rot - 1
        return rotation

    def move(self, Rotmax, moves, Rotate) -> str:
        """Computes the moving and rotating of the stl to the desired location."""
        rotation = [0, 0, 0]
        rotation = self.swapYZ(rotation, Rotate[0] / 90, Rotmax[1])
        rotation = self.swapXZ(rotation, Rotate[1] / 90, Rotmax[2])
        rotation = self.swapXY(rotation, Rotate[2] / 90, Rotmax[0])

        output = (
            "translate(["
            + str(rotation[0] + moves[0])
            + ", "
            + str(rotation[1] + moves[1])
            + ", "
            + str(rotation[2] + moves[2])
            + "])"
        )
        output = (
            output
            + "rotate(["
            + str(Rotate[0])
            + ", "
            + str(Rotate[1])
            + ", "
            + str(Rotate[2])
            + "])"
        )
        return output

    def colour(self, colour: str):
        """gives the colour."""
        return 'color("' + colour + '")'

    def assembly_stl(self):
        """decodes the provided scad and moves the object around as required, making a new scad."""
        out_name = "./SCAD/" + self.part_no + ".scad"
        SCAD = open(out_name, "w")
        in_name = "./JSON/" + self.part_no + ".json"
        with open(in_name) as f:
            data = json.load(f)
        f.close()

        output = []
        dif = 0
        end = False
        for action in data:
            output.append(
                self.move(action["rotmax"], action["moves"], action["rotate"])
            )
            output.append(self.colour(action["colour"]))
            output.append(self.fetch_part(action["part_no"]))

        for out in output:
            SCAD.write(out)

        SCAD.close()
