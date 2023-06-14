#!/usr/bin/env python3

from typing import Tuple

class CycaxSide:

    def __init__(self, parent):
        self._parent = parent

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Side: " + self.name

    def hole(self, pos, diameter: float, depth: float = None):
        _depth = self._depth_check(depth)
        print("Make a hole on the {} side".format(self.name) + "depth=" + str(_depth))

    def box(self, pos: Tuple[float, float], length: float, width: float, depth:float = None):
        _depth = self._depth_check(depth)
        print("Cut a box on the {} side".format(self.name) + "depth=" + str(_depth))


    def _depth_check(self, val: float):
        raise ValueError("_depth_check is Not implimented on" + self.name)

class LeftSide(CycaxSide):
    name = 'LEFT'

    def _box_calculation_bal_s(self, val):
        return val +1
    
    def _depth_check(self, val: float):
        if val is None:
            return self._parent.x_size
        else:
            return val

class RightSide(CycaxSide):
    name = 'RIGHT'
    def _box_calculation_bal_s(self, val):
        return val +5
   
    def _depth_check(self, val: float):
        if val is None:
            return self._parent.x_size
        else:
            return val

class TopSide(CycaxSide):
    name = 'TOP'

    def _depth_check(self, val: float):
        if val is None:
            return self._parent.z_size
        else:
            return val

class Part:

    def __init__(self):
        self.left = LeftSide(self)
        self.right = RightSide(self)
        self.top = TopSide(self)
        self.x_size = 100
        self.y_size = 100
        self.z_size = 100


if __name__ == "__main__":

    p = Part()
    print(p.left)
    print(p.right)

    p.left.hole((3,3), 7)
    p.top.hole((3,3), 7)



