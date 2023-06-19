#!/usr/bin/env python3

from cycax.cycad.engine_openscad import EngineOpenSCAD
from cycax.cycad.figure import Figure


class Render:
    """This class will render the necessary diagrams when called with the following methods. It is invoked int CycadPart and can be called: CycadPart.render.pyplot(left)."""
    
    def __init__(self, parent):
        self._parent = parent
        
    def pyplot(self, side: str):
        """This method will produce a pyplot of the specified side of the given object.
        
        Args:
            side: this is the side which the pyplot should be produced of.
        """
        plotter = Figure(part_no=self._parent.part_no, side=side)
        plotter.save_as_figure()
        
    def OpenSCAD(self):
        """This method will produce an OpenSCAD 3D drawing of the given object."""
        cutter = EngineOpenSCAD()
        cutter.decode(self._parent)
        
    def STL(self):
        """This method will convert a OpenSCAD drawing of a given file into a STL drawing."""
        cutter = EngineOpenSCAD()
        cutter.render_stl(self._parent)