import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, PathPatch, Polygon, Rectangle, Wedge
from matplotlib.path import Path


def get_feature_style(feature):
    """Return a dict with the style used by Matplotlib add_patch"""

    action = feature.get("type")
    if action == "cut":
        return {"color": "red", "edgecolor": "red", "alpha": 0.4}
    elif action == "add":
        return {"color": "grey", "edgecolor": "grey", "alpha": 0.6}
    elif action == "outline":
        return {"color": None, "edgecolor": "green", "alpha": 1, "fill": False}
    else:
        return {"color": "blue", "edgecolor": "blue", "alpha": 0.6}


# def slot(ax, feature):
#     ax.add_patch(
#         Circle(
#             (feature["x1"], feature["y1"]),
#             feature["radius"],
#             **get_feature_style(feature)
#         )
#     )
#     ax.add_patch(
#         Circle(
#             (feature["x2"], feature["y2"]),
#             feature["radius"],
#             **get_feature_style(feature)
#         )
#     )
#     if feature["vertical"]:
#         x = feature["x1"] - feature["radius"]
#         y = feature["y1"]
#     else:
#         x = feature["x1"]
#         y = feature["y1"] - feature["radius"]
#     length = feature["x2"] - feature["x1"]
#     width = feature["y2"] - feature["y1"]
#     if width == 0:
#         width = 2 * feature["radius"]
#     ax.add_patch(Rectangle((x, y), length, width, **get_feature_style(feature)))


def hole(ax, feature):
    ax.add_patch(Circle((feature["x"], feature["y"]), feature["diameter"] / 2, **get_feature_style(feature)))


def box(ax, feature):
    length = feature["y_size"]
    width = feature["x_size"]
    ax.add_patch(Rectangle((feature["x"], feature["y"]), length, width, **get_feature_style(feature)))


# def cut_feature(ax, feature):
#     feature_type = feature["type"]
#     if feature_type == "slot":
#         slot(ax, feature)
#     elif feature_type == "box":
#         box(ax, feature)
#     elif feature_type == "hole":
#         hole(ax, feature)


def figure_feature(ax, feature):
    feature_type = feature["type"]
    # if feature_type == "slot":
    #     slot(ax, feature)
    if feature_type == "box":
        box(ax, feature)
    elif feature_type == "hole":
        hole(ax, feature)


def save_as_figure(data):
    fig, ax = plt.subplots()
    # ax.add_patch(
    #     Rectangle(
    #         (0, 0),
    #         data["x_size"],
    #         data["y_size"],
    #         color="black",
    #         edgecolor="black",
    #         alpha=0.2,
    #     )
    # )
    # for feature in data.get("features_cut", []):
    #     cut_feature(ax, feature)
    for feature in data.get("features", []):
        figure_feature(ax, feature)
    ax.set_title("Partno. fix me")
    ax.autoscale_view()
    ax.set_aspect("equal", "box")
    # Path(data["base_path"])
    figfile = "./figures/{}-fig.svg".format(data["name"])
    plt.savefig(figfile)
    logging.info("Write to %s", figfile)
