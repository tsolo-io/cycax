from cycax.cycad.features import Holes, RectangleCutOut


class RoundedCorner:
    """This class will store data relating to the rounding of corners on a cube.
    
    Args:
        type: This is either a bevil or taper.
        axis1: This is an axis bounding the corner.
        bound1: The bound of the first axis.
        axis2: This is an axis bounding the corner.
        bound2: The bound of the second axis.
    """
    def __init__(self, corner_type: str, axis1: str, bound1: float, axis2:str, bound2: float, radius:float, side: str, depth: float):
        self.corner_type=corner_type
        self.axis1=axis1 
        self.bound1=bound1
        self.axis2=axis2
        self.bound2=bound2
        self.radius=radius
        self.side=side
        self.depth=depth
        
    def export(self) -> dict:
        """
        This will create a dictionary of the rectangle cut out that can be used for the json.

        Returns:
            dict: this will return a dictionary.

        """
        dict_corner = {}
        dict_corner["name"] = "rounded_corner"
        dict_corner["type"] = "cut"
        for key, value in vars(self).items():
            dict_corner[key] = value
        return dict_corner

  