from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, TOP

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