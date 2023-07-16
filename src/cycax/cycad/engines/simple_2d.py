import json
import logging
import os
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch, Polygon, Rectangle, Wedge
from matplotlib.path import Path

from cycax.cycad.engines.base_part_engine import PartEngine
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP

x = "x"
y = "y"
z = "z"


class Simple2D(PartEngine):
    """This is a class that will be used to draw pyplots of various views of a 3D object.

    Args:
        name: This is the name of the json file that needs to be decoded.
        side: Thi argument will suggest which side of the object the view is of.

    """

    def __init__(self, name, path: Path = None, config: dict = None):
        super().__init__(name, path, config)

        self.side = "TOP"
        if self.config is not None:
            if "side" in self.config:
                self.side = self.config["side"]

        self.plane = ""
        self.hole_sink = ""

        self.boundin_box = {
            BOTTOM: 0,
            TOP: 0,
            LEFT: 0,
            RIGHT: 0,
            FRONT: 0,
            BACK: 0,
        }

    def _get_feature_style(self, feature: dict) -> dict:
        """Return a dict with the style used by Matplotlib add_patch

        Args:
            feature: this is a dict that contains the details of the drawing

        """
        action = feature.get("type")
        if action == "add":
            return {"color": "grey", "edgecolor": "grey", "alpha": 0.6}
        elif action == "cut":
            return {"color": "red", "edgecolor": "red", "alpha": 0.4}
        elif action == "outline":
            return {"color": None, "edgecolor": "green", "alpha": 1, "fill": False}
        else:
            return {"color": "blue", "edgecolor": "blue", "alpha": 0.6}

    def bounding_box(self, feature: dict):
        """This method will update the bounding box of a feature when called. It is also used to update other information with regards to the plane of the odject that is affected by the side.

        Args:
            feature: this is the dictionary that contains the details of the object being produced.
        """
        self.boundin_box[TOP] = self.boundin_box[TOP] + feature["z_size"]
        self.boundin_box[RIGHT] = self.boundin_box[RIGHT] + feature["x_size"]
        self.boundin_box[BACK]: self.boundin_box[BACK] + feature["y_size"]
        self.plane = self.side
        self.hole_sink = self.side
        self.plane = {TOP: z, BACK: y, BOTTOM: z, FRONT: y, LEFT: x, RIGHT: x}[self.plane]
        self.hole_sink = {
            TOP: "depth",
            BACK: "diameter",
            BOTTOM: "depth",
            FRONT: "diameter",
            LEFT: "diameter",
            RIGHT: "diameter",
        }[self.hole_sink]

    def _hole(self, ax: matplotlib.axes._axes.Axes, feature: dict):
        """This method will draw a hole on the plot if the given hole reaches the side which it is drawing.

        Args:
            ax: this is the axes onto which the object will be drawn.
            feature: this is the dictionary of the object that is being plotted.
        """
        if (
            feature[self.plane] == self.boundin_box[self.side]
            or feature[self.plane] + feature[self.hole_sink] == self.boundin_box[self.side]
            or feature[self.plane] - feature[self.hole_sink] == self.boundin_box[self.side]
        ):
            ax.add_patch(
                Circle((feature["x"], feature["y"]), feature["diameter"] / 2, **self._get_feature_style(feature))
            )

    def _box(self, ax: matplotlib.axes._axes.Axes, feature: dict):
        """This method will draw a box on the plot if the given cube reaches the side which it is drawing. It uses a dict to figure out the dimentions of the box it is drawing.

        Args:
            ax: this is the axes onto which the object will be drawn.
            feature: this is the dictionary of the object that is being plotted.
        """
        if (
            feature[self.plane] == self.boundin_box[self.side]
            or feature[self.plane] + feature[self.plane + "_size"] == self.boundin_box[self.side]
            or feature[self.plane] - feature[self.plane + "_size"] == self.boundin_box[self.side]
        ):
            length = self.side
            length = {
                TOP: "x_size",
                BACK: "x_size",
                BOTTOM: "x_size",
                FRONT: "x_size",
                LEFT: "y_size",
                RIGHT: "y_size",
            }[length]
            width = self.side
            width = {
                TOP: "y_size",
                BACK: "z_size",
                BOTTOM: "y_size",
                FRONT: "z_size",
                LEFT: "z_size",
                RIGHT: "z_size",
            }[width]
            length = feature[length]
            width = feature[width]
            ax.add_patch(Rectangle((feature["x"], feature["y"]), length, width, **self._get_feature_style(feature)))

    def figure_feature(self, ax: matplotlib.axes._axes.Axes, feature: dict):
        """This method will coordingte the decoding of the dictionary.

        Args:
            ax: this is the axes onto which the object will be drawn.
            feature: this is the dictionary of the object that is being plotted.
        """
        feature_type = feature["name"]
        if feature_type == "cube":
            self._box(ax, feature)
        elif feature_type == "hole":
            self._hole(ax, feature)

    def build(self):
        """This method will coordinate the drawing and saving of the figure that is being decoded from the provided json."""
        in_name = self._json_file
        with open(in_name) as f:
            data = json.load(f)
        fig, ax = plt.subplots()
        for feature in data["features"]:
            if feature["type"] == "add":
                self.bounding_box(feature)
            self.figure_feature(ax, feature)
        ax.set_title(self.name)
        ax.autoscale_view()
        ax.set_aspect("equal", "box")
        figfile = figfile = self._base_path / self.name / (self.name + "-s2d.svg")
        plt.savefig(figfile)
        logging.info("Write to %s", figfile)
