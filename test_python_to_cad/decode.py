import json
import subprocess


class decode:
    dif = 0

    def decode_cube(self, lookup: dict) -> str:
        """This method will return the string that will have the scad for a cube."""
        center = ""
        if lookup["center"] == True:
            center = ", center=true"
        res = (
            "cube(["
            + str(lookup["X_width"])
            + ", "
            + str(lookup["Y_length"])
            + ","
            + str(lookup["Z_depth"])
            + "]"
            + center
            + ");"
        )
        return res

    def decode_hole(self, lookup: dict) -> str:
        """This method will return the string that will have the scad for a hole."""
        tempdiam = lookup["diameter"] / 2
        res = (
            "cylinder(r=" + str(tempdiam) + ", h=" + str(lookup["depth"]) + ", $fn=64);"
        )
        return res

    def decode_nut(self, lookup: dict) -> str:
        """This method will return the string that will have the scad for a nut cut out."""
        res = (
            "rotate(["
            + str(0)
            + ", "
            + str(0)
            + ", "
            + str(0)
            + "])"
            + "cylinder(r="
            + str(lookup["diameter"])
            + ", h="
            + str(lookup["depth"])
            + ", $fn=6);"
        )
        return res

    def decode_cut(self) -> str:
        """This method returns a simple scad string neceseray to cut."""
        return "difference(){"

    def translate(self, lookup: dict) -> str:
        """This will move the object around and return the scad necessary."""
        res = (
            "translate(["
            + str(lookup["x"])
            + ", "
            + str(lookup["y"])
            + ", "
            + str(lookup["z"])
            + "])"
        )
        return res

    def rotate(self, side: str) -> str:
        """This will rotate the object and return the scad necessary."""
        if side == "TOP":
            return "rotate([" + str(0) + ", " + str(180) + ", " + str(0) + "])"
        if side == "BOTTOM":
            return "rotate([" + str(0) + ", " + str(0) + ", " + str(0) + "])"
        if side == "LEFT":
            return "rotate([" + str(0) + ", " + str(90) + ", " + str(0) + "])"
        if side == "RIGHT":
            return "rotate([" + str(0) + ", " + str(270) + ", " + str(0) + "])"
        if side == "FRONT":
            return "rotate([" + str(270) + ", " + str(0) + ", " + str(0) + "])"
        if side == "BACK":
            return "rotate([" + str(90) + ", " + str(0) + ", " + str(0) + "])"
        else:
            return None

    def move(self, Rotation, moves) -> str:
        """This class co ordinates the final position of objects. It was used betofr assembly_stl and should be depricated."""
        output = (
            "translate(["
            + str(moves[0])
            + ", "
            + str(moves[1])
            + ", "
            + str(moves[0])
            + "])"
        )
        output = (
            output
            + "rotate(["
            + str(Rotation[0])
            + ", "
            + str(Rotation[1])
            + ", "
            + str(Rotation[2])
            + "])"
        )
        return output

    def decode(self, data_file):
        """This is the main working class for decoding the scad. It is necessary for it to be refactored."""
        out_name = "./SCAD/" + data_file + ".scad"
        SCAD = open(out_name, "w")
        in_name = "./JSON/" + data_file + ".json"
        with open(in_name) as f:
            data = json.load(f)

        output = []
        dif = 0
        end = False
        for action in data:
            if action["type"] == "cut":
                dif = dif + 1
                output.insert(0, self.decode_cut())

            output.append(self.translate(action))

            if "rotate" in action:
                end = True
                endoutput = self.move(action["rotate"], action["moves"])

            if action["side"] != None:
                output.append(self.rotate(action["side"]))

            if action["name"] == "cube":
                output.append(self.decode_cube(action))

            if action["name"] == "hole":
                output.append(self.decode_hole(action))

            if action["name"] == "nut":
                output.append(self.decode_nut(action))

        i = 0

        if end:
            output.insert(0, endoutput)

        while i < dif:
            i = i + 1
            output.append("}")

        for out in output:
            SCAD.write(out)

        SCAD.close()

    def render_stl(self, filename: str):
        """This takes a SCAD object and runs a command through linex that converts it into an stl. Depending on the complexity of the object it can take long to compute."""
        out_name = "./SCAD/" + filename + ".scad"
        out_stl_name = "./STL/" + filename + ".stl"

        print("!!! THIS WILL TAKE SOME TIME, BE PATIENT !!!")
        result = subprocess.run(
            ["openscad", "-o", out_stl_name, out_name], capture_output=True, text=True
        )
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
