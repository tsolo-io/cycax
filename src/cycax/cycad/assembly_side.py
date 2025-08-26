from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP


class AssemblySide:
    name = ""

    def __init__(self, parent):
        self._parent = parent

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Side: " + self.name

    def _rotate(self):
        """
        Rotate the assembly by 90 degrees by keeping selected side on the same plain.
        """
        msg = "_rotate should be defined for each side."
        raise NotImplementedError(msg)

    def rotate(self, angle: float = 90):
        """
        Rotate the assembly by keeping the selected side on the same plain.

        Rotation is counter clock wise. Negative angles are converted to positive.

        Args:
            angle: The angle in degrees that the assembly will be rotates on.
        """
        if angle % 90 != 0:
            # TODO: Think about which exception should be raised, maybe even a custom one.
            msg = "Can only rotate in multiples of 90 degrees"
            raise ValueError(msg)

        while angle < 0:
            # Change the angle to a positive number.
            angle = 360 + angle

        for _n in range(int(angle / 90)):
            self._rotate()

    def level(self, assembly_side: str):
        """
        Align the two sides onto the same plain.

        Moves assembly1 so that its given side is on the same plain as the given
        side of assembly2. e.g. `level(assembly1.front assembly2.back)` will move assembly1
        so that its front is on the same plain as the back of assembly2.

        Args:
            assembly1: The Assembly to be moved to match the plain of the other assembly.
            assembly2: The Assembly used as reference when moving assembly1.
        Raises:
            ValueError: When the side present in Assembly does not match one of the expected sides.
        """
        assembly1_side = self.name
        assembly2_side = assembly_side.name
        assembly1 = self._parent
        assembly2 = assembly_side._parent
        if assembly1_side not in SIDES or assembly2_side not in SIDES:
            msg = f"Side: {assembly1_side} or Side: {assembly2_side} is not one of {SIDES}"
            raise ValueError(msg)

        assembly1_bounding_box = assembly1.bounding_box
        assembly2_bounding_box = assembly2.bounding_box
        to_here = assembly2_bounding_box[assembly2_side]

        if assembly1_side == BOTTOM:
            assembly1.at(z=to_here)
        elif assembly1_side == TOP:
            z_size = assembly1_bounding_box[TOP] - assembly1_bounding_box[BOTTOM]
            assembly1.at(z=to_here - z_size)
        elif assembly1_side == LEFT:
            assembly1.at(x=to_here)
        elif assembly1_side == RIGHT:
            x_size = assembly1_bounding_box[RIGHT] - assembly1_bounding_box[LEFT]
            assembly1.at(x=to_here - x_size)
        elif assembly1_side == FRONT:
            assembly1.at(y=to_here)
        elif assembly1_side == BACK:
            y_size = assembly1_bounding_box[BACK] - assembly1_bounding_box[FRONT]
            assembly1.at(y=to_here - y_size)
        else:
            msg = f"Side: {assembly1_side} is not one of {SIDES}."
            raise ValueError(msg)

    def subtract(self, assembly2):  # Using the Assembling in the description creates a circular import.
        """
        Loops through the parts in each assembly and adds the features from assembly2 that touch the face of assembly1.

        Args:
            assembly1: The assembly that you add the features to.
            assembly1_side: The side of the assembly that you add features to.
            assembly2: The assembly that is used as the template when transferring features.
        """
        assembly1 = self._parent
        assembly1_side = self.name
        for part1 in assembly1.parts.values():
            if assembly1_side == TOP:
                for part2 in assembly2.parts.values():
                    if part2._name in assembly2.external_feature_parts:
                        part1.top.subtract(part2=part2)
            elif assembly1_side==BOTTOM:
                for part2 in assembly2.parts.values():
                    if part2._name in assembly2.external_feature_parts:
                        part1.bottom.subtract(part2=part2)
            elif assembly1_side==LEFT:
                for part2 in assembly2.parts.values():
                    if part2._name in assembly2.external_feature_parts:
                        part1.left.subtract(part2=part2)
            elif assembly1_side==RIGHT:
                for part2 in assembly2.parts.values():
                    if part2._name in assembly2.external_feature_parts:
                        part1.right.subtract(part2=part2)
            elif assembly1_side==FRONT:
                for part2 in assembly2.parts.values():
                    if part2._name in assembly2.external_feature_parts:
                        part1.front.subtract(part2=part2)
            elif assembly1_side==BACK:
                for part2 in assembly2.parts.values():
                    if part2._name in assembly2.external_feature_parts:
                        part1.back.subtract(part2=part2)
            else:
                msg = f"{assembly1_side} not in {SIDES}."
                raise ValueError(msg)


class LeftSide(AssemblySide):
    name = LEFT

    def _rotate(self):
        self._parent.rotate_freeze_left()


class RightSide(AssemblySide):
    name = RIGHT

    def _rotate(self):
        self._parent.rotate_freeze_left()


class TopSide(AssemblySide):
    name = TOP

    def _rotate(self):
        self._parent.rotate_freeze_top()


class BottomSide(AssemblySide):
    name = BOTTOM

    def _rotate(self):
        self._parent.rotate_freeze_top()


class FrontSide(AssemblySide):
    name = FRONT

    def _rotate(self):
        self._parent.rotate_freeze_front()


class BackSide(AssemblySide):
    name = BACK

    def _rotate(self):
        self._parent.rotate_freeze_front()
