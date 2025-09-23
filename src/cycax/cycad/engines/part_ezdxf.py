import ezdxf

from pathlib import Path

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
