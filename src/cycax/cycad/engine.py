import json
import subprocess
import logging
from cycax.cycad.location import TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK
from cycax.cycad.cycad_part import CycadPart

class Engine:
    """
    This class willbe used to decode a json to a scad file which can be rendered in openscad for 3D view.
    """
    dif = 0

    def decode_cube(self, lookup: dict)->str:
        """
        This method will return the string that will have the scad for a cube.
        
        Args:
            lookup: this will be the dictionary that contains the details about the cube so that is can be encoded in scad.
            
        """
        center = ""
        if lookup["center"] == True:
            center = ", center=true"
        res = (
            "cube(["
            + str(lookup["x_size"])
            + ", "
            + str(lookup["y_size"])
            + ","
            + str(lookup["z_size"])
            + "]"
            + center
            + ");"
        )
        return res
    
    def decode_external(self, data_file: str)->str:
        """
        This method will return the scad string necessary for processing the external part.
        
        Args:
            data_file : This will contain the part number of the external part so that it can be fetched from the parts_stl folder. 
              
        """
        
        return 'import("../parts_stl/' + data_file + '.stl");'

    def decode_hole(self, lookup: dict)->str:
        """
        This method will return the string that will have the scad for a hole.
        
        Args: 
            lookup : This will be a dictionary containing the necessary information about the hole.
            
        """
        tempdiam = lookup["diameter"] / 2
        res = (
            "cylinder(r=" + str(tempdiam) + ", h=" + str(lookup["depth"]) + ", $fn=64);"
        )
        return res

    def decode_nut(self, lookup: dict)->str:
        """
        This method will return the string that will have the scad for a nut cut out.
        
        Args:
            lookup : This will be a dictionary containing the necessary information about the nut.
            
        """
        res = (
            "rotate(["
            + str(0)
            + ", "
            + str(0)
            + ", "
            + str(0)
            + "])"
            + "cylinder(r="
            + str(lookup["nut_type"])
            + ", h="
            + str(lookup["depth"])
            + ", $fn=6);"
        )
        return res

    def decode_cut(self)->str:
        """
        This method returns a simple OpenSCAD string neceseray to cut.
        """
        return "difference(){"

    def translate(self, lookup: dict)->str:
        """
        This will move the object around and return the scad necessary.

        Args:
            lookup : This will be a dictionary containing the necessary information about the hole.
        """
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

    def rotate(self, side: str)->str:
        """
        This will rotate the object and return the scad necessary.
        
        ???Would it make sense to also have a dictionary here similar to location swap methods???
        
        Args:
            side : this is the side as retrieved form the dictionary. 
        """
        if side == TOP:
            return "rotate([" + str(0) + ", " + str(180) + ", " + str(0) + "])"
        elif side == BOTTOM:
            return "rotate([" + str(0) + ", " + str(0) + ", " + str(0) + "])"
        elif side == LEFT:
            return "rotate([" + str(0) + ", " + str(90) + ", " + str(0) + "])"
        elif side == RIGHT:
            return "rotate([" + str(0) + ", " + str(270) + ", " + str(0) + "])"
        elif side == FRONT:
            return "rotate([" + str(270) + ", " + str(0) + ", " + str(0) + "])"
        elif side == BACK:
            return "rotate([" + str(90) + ", " + str(0) + ", " + str(0) + "])"
        else:
            msg = f"Side: {side} is not one of TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK."
            raise ValueError(msg)


    def decode(self, data_file: str):
        """
        This is the main working class for decoding the scad. It is necessary for it to be refactored.
        
        !!!For this method to work properly it will be necessary to add a JSON, STL and SCAD file into the working repository.!!!
        
        Args: 
            data_file : name of the file that is to be decoded into a scad.
        """
        out_name = "./SCAD/" + data_file + ".scad"
        SCAD = open(out_name, "w")
        in_name = "./JSON/" + data_file + ".json"
        
        with open(in_name) as f:
            data = json.load(f)

        output = []
        dif = 0
        for action in data:
            if action["type"] == "cut":
                dif = dif + 1
                output.insert(0, self.decode_cut())

            output.append(self.translate(action))


            if action["side"] != None:
                output.append(self.rotate(action["side"]))

            if action["name"] == "cube":
                output.append(self.decode_cube(action))

            if action["name"] == "external":
                output.append(self.decode_external(data_file))

            if action["name"] == "hole":
                output.append(self.decode_hole(action))

            if action["name"] == "nut":
                output.append(self.decode_nut(action))

        i = 0
        while i < dif:
            i = i + 1
            output.append("}")

        for out in output:
            SCAD.write(out)

        SCAD.close()

    def render_stl(self, filename: str):
        """
        
        This takes a SCAD object and runs a command through linex that converts it into an stl. 
        Depending on the complexity of the object it can take long to compute.
        It prints out some messages to the terminal so that the impatient user will hopefully wait.(Similar to many windows request.)
        
        Args:
            filename : This is the name of the file which will be converted from a scad to a stl
        
        """
        out_name = "./SCAD/" + filename + ".scad"
        out_stl_name = "./STL/" + filename + ".stl"

        print("!!! THIS WILL TAKE SOME TIME, BE PATIENT !!!")
        result = subprocess.run(
            ["openscad", "-o", out_stl_name, out_name], capture_output=True, text=True
        )
        
        if result.stdout:
            logging.info('OpenSCAD: %s', result.stdout)
        if result.stderr:
            logging.error('OpenSCAD: %s', result.stderr)
        
    def add(self, part):
        """
        This takes the provided part and will create its dictionary and export it to a json
        
        Args:
            part(CycadPart) : This is the part that will be eported to a json.  
        """
        
        with open("./JSON/" + part.part_no + ".json", "w") as jsonfile:
            json.dump(part.export(), jsonfile, indent=4)
