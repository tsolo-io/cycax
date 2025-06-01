# SPDX-FileCopyrightText: 2025 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0


class BeveledEdge:
    """This class will store data relating to the rounding of edges on a cube.

    Args:
        edge_type: This is either a bevil or taper.
        axis1: This is an axis bounding the edge.
        bound1: The bound of the first axis.
        axis2: This is an axis bounding the edge.
        bound2: The bound of the second axis.
    """

    def __init__(
        self,
        edge_type: str,
        axis1: str,
        bound1: float,
        axis2: str,
        bound2: float,
        size: float,
        side: str,
        depth: float,
    ):
        self.edge_type = edge_type
        self.axis1 = axis1
        self.bound1 = bound1
        self.axis2 = axis2
        self.bound2 = bound2
        self.size = size
        self.side = side
        self.depth = depth

    def export(self) -> dict:
        """
        This will create a dictionary of the rectangle cut out that can be used for the JSON.

        Returns:
            this will return a dictionary.

        """
        dict_edge = {}
        dict_edge["name"] = "beveled_edge"
        dict_edge["type"] = "cut"
        for key, value in vars(self).items():
            dict_edge[key] = value
        return dict_edge
