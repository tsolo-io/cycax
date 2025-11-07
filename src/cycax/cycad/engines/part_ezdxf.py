from pathlib import Path
from math import pi
import ezdxf
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP


OUTLINE = "Outline"
CIRCLES = "Circles"
BENDS = "Bends"
LAYERS = (OUTLINE, CIRCLES, BENDS)


class PartEzdxfEngine:
    """
    Decode the 2D information in a json file to create a dxf file that displays sheetmetal bends.
    """

    def __init__(self, name: str | None = None, path: Path | None = None, config: dict | None = None):
        self.name = name
        self.path = path
        self.config = config
        self.__calc__()
        self.side_details = {}

    def __calc__(self):
        self.doc = ezdxf.new(setup=True)  # setup required line types
        self.doc.layers.add(name=OUTLINE, color=7, linetype="SOLID")
        self.doc.layers.add(name=CIRCLES, color=3, linetype="SOLID")
        self.doc.layers.add(name=BENDS, color=1, linetype="DASHED")
        self.msp = self.doc.modelspace()

    def save(self):
        """
        Export and save as a dxf.
        """
        file_name = self.path / f"{self.name}.dxf"
        self.doc.saveas(file_name)

    def line(self, start: tuple, end: tuple, layer: str):
        """
        Draw a line in the desired layer.

        Args:
            start: (x, y) Where to start the line from.
            end: (x, y) Where to end the line.
            layer: Layer to draw the line at.

        Raises:
            ValueError: Layer provided is not one of the defined layers.
        """
        if layer not in LAYERS:
            msg = f"{layer=} not one of the defined {LAYERS=}."
            raise ValueError(msg)
        self.msp.add_line(start, end, dxfattribs={"layer": layer})

    def box(self, location: tuple, length: float, width: float, layer: str):
        """
        Draw a box.

        Args:
            location: (x,y)
            length: Length of the box.
            width: width of the box.
        """
        start = None
        initial = None
        for x in (location[0], location[0]+width):
            for y in (location[1], location[1]+length):
                if not initial:
                    initial = (x, y)
                    start = (x, y)
                else:
                    self.line(start=start, end = (x,y), layer=layer)
                    start = (x, y)
        self.line(start=start, end = initial)



    def circle(self, location: tuple, radius: float, layer: str = CIRCLES):
        """
        Draw a circle in the desired layer.

        Args:
            location: (x, y) location of center of circle.
            radius: Radius of the circle.
            layer: Layer to draw the circle at.

        Raises:
            ValueError: Layer provided is not one of the defined layers.
        """
        if layer not in LAYERS:
            msg = f"{layer=} not one of the defined {LAYERS=}."
            raise ValueError(msg)
        self.msp.add_circle(location, radius=radius, dxfattribs={"layer": layer})

    def build_scad(self, json_file: Path, scad_file: Path):
        """
        This is the main working class for decoding the scad. It is necessary for it to be refactored.
        Raises:
            ValueError: if incorrect part_name is provided.
        """

        data = json.loads(json_file.read_text())

        output = []
        dif = 0
        for action in data["features"]:
            if action["name"] == "cube":
                if action["type"] == "add":
                    self.x_size = action["x_size"]
                    self.y_size = action["y_size"]
                    self.x_loc = action["x"]
                    self.y_loc = action["y"]
                    self.thickness = action["z_size"]
                else:
                    self.draw_cube(action)

            if action["name"] == "bend":
                bend(action = action)

            if action["name"] == "circle":

    def bend(self, action: dict, x_size, y_size, x_loc, y_loc):
        """
        Extend the bounding box of the sheetmetal and add the bend line.

        Args:
            action: Details of the bend.
        """
        side = action["side"]
        if side not in [FRONT, BACK, LEFT, RIGHT]:
            msg = f"Can only bend from sides {[FRONT, BACK, LEFT, RIGHT]}"
            raise ValueError(msg)
        angle = action["angle"]
        bend_radius = action["bend_radius"]
        k_factor = action["k_factor"]
        internal = action["internal"]
        height = action["height"]
        bend_allowance = self.bend_allowance_calc(side=side, angle=angle, bend_radius=bend_radius, k_factor=k_factor, internal=internal, height=height)
        # 1. calculate the bend allowance. 
        # 2. extend the bounding box and change valued of x_size, y_size, x_loc and y_loc
        # 3. Drave the bend line in the bend plane. 


    def bend_allowance_calc(self, side: str, angle: float, bend_radius: float, k_factor: float, internal: bool, height: float):
        """
        This function will perform calculations to create the flat sheet. 
        Calculations have been found here https://users.metu.edu.tr/sonmez/MECH%20114/Sheet%20Metal%20Work.pdf

        Args:
            angle (float): Angle to bend the sheet at.
            bend_radius (float): Radius of the bend.
            k_factor (float): (distance from inside face to neutral line) / thickness 
            height (float): Height of bend.
            side_length (float): Length of the side.
            internal (bool): Whether the bend is an add or internal.
        """
        bend_allowance = angle*(pi/180)*(bend_radius + k_factor * self.thickness)
        if (side == LEFT or side == RIGHT):
            side_length = self.x_size
        else:
            side_length = self.y_size
        if internal:
            added_sheet_b = height - bend_radius  - self.thickness
            original_sheet_b = side_length - bend_radius - self.thickness
        else:
            added_sheet_b = height - bend_radius
            original_sheet_b = side_length - bend_radius
        new_sheet = added_sheet_b + bend_allowance + original_sheet_b

        return bend_allowance
    
    def bounding_box_extention(self, side: str, bend_allowance: float):
        if side == LEFT:
            self.x_loc = self.x_loc - bend_allowance
            self.x_size = self.x_size + bend_allowance
        elif side == RIGHT:
            self.x_size = self.x_size + bend_allowance
        elif side == FRONT:
            self.y_loc = self.y_loc - bend_allowance
            self.y_size = self.y_size + bend_allowance
        else:
            self.y_size = self.y_size + bend_allowance



    
    def bend_line_calc(self, side: str, internal: bool, bend_radius: float, bend_allowance: float):
        if side == LEFT:
            if internal:
                x = self.x_loc - bend_allowance / 2
                y = self.y_loc 
            else:
                x = self.x_loc + bend_radius - bend_allowance / 2
                y = self.y_loc
            end = (x, y + self.y_size)
        elif side == RIGHT:
            if internal:
                x = self.x_loc + self.x_size + bend_allowance / 2
                y = self.y_loc
            else:
                x = self.x_loc - bend_radius + self.x_size + bend_allowance / 2
                y = self.y_loc
            end = (x, y + self.y_size)
        elif side == BACK:
            if internal:
                x = self.x_loc
                y = self.y_loc + self.y_size + bend_allowance / 2
            else:
                x = self.x_loc 
                y = self.y_loc - bend_radius + self.y_size + bend_allowance / 2
            end = (x + self.x_size, y)
        elif side == FRONT:
            if internal:
                x = self.x_loc
                y = self.y_loc - bend_allowance / 2
            else:
                x = self.x_loc 
                y = self.y_loc - bend_radius - bend_allowance / 2
            end = (x + self.x_size, y)
        self.side_details[side] = {"internal": internal, "bend_radius": bend_radius, "bend_allowance": bend_allowance}
        self.line(start = (x, y), end = end, layer = BENDS)


    def circle_in_part(self, side: str):
        if side not in self.side_details.keys():
            msg = f"{side=} is not a bent side in the part and therfore cannot receive a hole."
            raise ValueError(msg)
        radius = self.side_details[side]["radius"]
        bend_allowance = self.side_details[side]["bend_allowance"]
        if side == LEFT:
            x = self.x_loc - (x - self.thickness - radius) - bend_allowance #This should move us from c to b given c will be the specified.
        elif side == RIGHT:
            x = self.x_loc + self.x_size + (x - self.thickness - radius) + bend_allowance
        elif side == FRONT:
            y = self.y_loc - (y - self.thickness - radius) - bend_allowance 
        elif side == BACK:
            y = self.y_loc + self.y_size + (y - self.thickness - radius) + bend_allowance
        self.circle(location=(x, y), radius=radius)


# doc = ezdxf.new(setup=True)  # setup required line types
# msp = doc.modelspace()
# doc.layers.add(name="Outline", color=7, linetype="SOLID")
# doc.layers.add(name="Circles", color=3, linetype="SOLID")
# doc.layers.add(name="Bends", color=1, linetype="DASHED")
# msp.add_line((0, 0), (50, 0), dxfattribs={"layer": "Outline"})
# msp.add_line((0, 25), (50, 25), dxfattribs={"layer": "Bends"})
# msp.add_line((0, 50), (50, 50), dxfattribs={"layer": "Outline"})
# msp.add_line((0, 0), (0, 50), dxfattribs={"layer": "Outline"})
# msp.add_line((50, 0), (50, 50), dxfattribs={"layer": "Outline"})
# msp.add_circle(center=(20, 18), radius=5, dxfattribs={"layer": "Circles"})
# msp.add_circle((10, 10), radius=3, dxfattribs={"layer": "Circles"})
# doc.saveas("test.dxf")
