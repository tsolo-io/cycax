


# For sheetmetal length, width, thickness dont change on rotate. x_size, y_size, z_side do change with rotate and flip.
# At init length, width, thickness = x_size, y_size, z_side.

# each object has method: Use a @property decorator on a method to create a getter or look at https://pyviz-dev.github.io/param/index.html
# - x_min - x point closest to origin
# - x_max - x point furthest from origin
# - y_min,z_min,y_max,z_max same as x_ methods.

class Hole(Feature):
    # A cylinder drilled in from a side.
    # Always open on one side. The specified side is the open side, where you drill from.
    # If no depth is given it goes through all the way.
    # Optional definition thread, to specify the thread type as a string.
    # Would this be the right place to add counter sunk info. e.g. countersunk_diameter=6. We will take countersunk angle to always be a constant 45Deg.
    # With countersunk is this 1 or 2 features? A cylinder and a cone. Would like to see two circles on the preview we make with matplot lib.
    # https://wiki.freecad.org/PartDesign_Hole
    # https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Primitive_Solids section on cylinders

class Slot(Feature):
    # A rectangle cut with holes at the end, holes diameter is the width of rectangle.
    # Not an oval. Not a rectangle with rounded corners.
    # Has an angle.
    # Simplest reference point might be the center if the one circle.
    # Maybe: s = Slot(x=10, y=10, length=20, radius=5, angle=90) 
    # Then middle of the two circles are 20mm apart.
    # First circle at (10,10) with diameter=10.
    # Second circle at (10,30) with diameter=10.
    # Rectangle (5,10) to (15,30).
    # This will be 3 features.

class Cut_a_nut(Feature):
    # Please lets rename. Maybe just Nut.
    # A pentagonal prism I think. Has 6 sides, or if you want to add top and bottom then it has 8 sides.
    # Orientation? Maybe always flat on the given side. So from given side you see a hexagon.
    # Rotation. Does one of the corners point down or is two of the sides horizontal.
    # Reference point: When I think of a nut placement the center of the bottom makes most sense.
    # type=M2,M2.5,M3,M4,M5,.... makes sense. This will give us the size of the Nut. https://amesweb.info/Fasteners/Nut/Metric-Hex-Nut-Sizes-Dimensions-Chart.aspx
    # Since the nut is deep in the ConnCube it needs an x,y, and z pos relative to the given side.
    # NOT: a Pocket of a polygon, https://wiki.freecad.org/PartDesign_Pocket 
    # In OpenSCAD this can be done by making a low resolution cylinder e.g. circle(10, $fn=6)
    # Or more precise by defining a polyheadron.
    # Or by importing some library that has nuts defined. (I'll be reluctant since that creates a dependency but we can talk about it)

class ConnCube(Printed3d):

    x_size = 11 # Length
    y_size = 11 # Width
    z_size = 11 # Height
    # Maybe length, width, height is friendlier names than [xyz]_size.

    def calculate(self):
        # Some function that is always called by __init__.

        # Make a 3.2mm hole from the left 2mm deep at x=7 and y=7 on the left plane.
        # Make a 3.2mm hole from the bottom 2mm deep at x=7 and y=7 on the bottom plane.
        # Make a 3.2mm hole from the front 2mm deep at x=7 and y=7 on the front plane.
        # etc.
        for side in (LEFT, BOTTOM, FRONT):
            self.add_feature(Hole(side, x=7, y=7, diameter=3.2, depth=2))
            self.add_feature(Hole(side, x=7, y=7, diameter=2.9)) # Through everything
            # Two holes for the bolt. The bolt go into a slightly bigger hole, then through the nut then a tight hole to act like a thread lock.
            
        for side in (TOP, RIGHT, REAR):
            self.add_feature(HoleThatIsNotRound(side, x=1, y=1, length=2, width=6.2, depth=7)) # Cut a rectangle hole. Pocket of a rectangled, RectPocket maybe. Coordinates based on anker corner.
            self.add_feature(Cut_a_nut(side, x=7, y=7, z=2)) # Coordinates based on center of the Nut.

        # Cut the excess material we dont want to print.
        self.add_feature(HoleThatIsNotRound(TOP, x=4, y=4, length=100, width=100, depth=self.z_size-4))
        # Above 1 line is a simplification. I cut 3 cubes and 3 holes to get a nice round joins, but thats finer details.
        # Internaly features are added for the outline of the part. A rectangle on each side. This will always be 6 rectangles.


    def alt_calculate(self) -> Iterable[Feature]:
        """An alternative to calculate, it could be much nicer if calculate were an iterator that produces Features.

        Note: we will have calculate or alt_alculate not both. Although using self.add_feature in calculate would not be wrong jus wierd....
        In the base class you would just do.
        for feature in self.calculate():
            self.add_feature(feature)
        """
        for side in (LEFT, BOTTOM, FRONT):
            yield Hole(side, x=7, y=7, diameter=3.2, depth=2)
            yield Hole(side, x=7, y=7, diameter=2.9)

        for side in (TOP, RIGHT, REAR):
            yield HoleThatIsNotRound(side, x=1, y=1, length=2, width=6.2, depth=7)
            yield Cut_a_nut(side, x=7, y=7, z=2, point_down=True)

        # Cut the excess material we dont want to print.
        yield HoleThatIsNotRound(TOP, x=4, y=4, length=100, width=100, depth=self.z_size-4)

class FrontPanel(SheetMetal):

    x_size = 100
    y_size = 230
    thickness = 2 # Or should be import AluminiumSheet2mm, to hard to spell.

    def calculate(self):

        fan1 = Fan8025(slotted_vent=True) # 80mm x 80mm fan that is 25mm thick.
        vent = {'type': 'slotted', 'side': TOP, 'horisontal': True} # Horizontal slots.
        vent = {'type': 'flower', 'side': TOP} # Radial layout of asymmetrical slots.
        vent = {'type': 'hole', 'side': TOP} # One big hole, e.g. internal fans.
        fan2 = Fan8025(vent=vent) # Then the vent is a property on the Fan. if vent=None then only the screw holes and outline will be a feature.
        fan1.center_at(x=self.x_size/2, y=11)
        fan2.center_at(x=self.x_size/2, y=11+fan1.height+14)
        for fan in (fan1, fan2):
            self.add_features(fan.features()) # Note plural

def sheetmetal_factory(length, width):
    sheet = Sheetmetal()
    sheet.lenght = lenth
    sheet.width = width
    sheet.thickness = 2
    return sheet

def main():
    system = Assembly()
    front = FrontPanel()
    top = sheetmetal_factory(750, front.width - 2*front.thickness)
    left = sheetmetal_factory(750, 230)
    right = sheetmetal_factory(750, 230)
    
    front.rotate_x(90) # Flip from xy plane to xz plane. TOP is now the FRONT.
    cube1 = ConnCube() # or cubes=[]; cubes.append(ConnCube())
    cube1.rotate_y(90).at(y=front.thickness)
    cube2 = ConnCube()
    cube2.rotate_y(180).at(front.thickness)
    z = front.height-cube1.height-top.thickness
    cube1.at(z=z)
    cube2.at(z=z)
    cube1.at(x=left.thickness)
    cube2.at(x=front.x_size-right.thickness-cube2.x_size)
    # OR use constraints. We dont save the constraint. Only use it to improve the language.
    top.bottom.coincident(cube1.bottom) # Rotate cube1 until its bottom is on the same plane as top. https://wiki.freecad.org/A2plus_Workbench#Plane_on_Plane
    top.bottom.touch(cube1.bottom)
    # Now do something to get cube features and subtract that from front.
    # This makes me think that all parts has an imutable length, width, height or thickness for sheetmetal. But as the part gets rotates the x_size, y_size, z_size changes.
    # On part init self.x_size = copy(self.length) etc......

    system.add(front)
    system.add(top)
    system.add(left)
    system.add(right)
    system.add(cube1)
    system.add(cube2)
    system.save() # This creates the JSON file.
