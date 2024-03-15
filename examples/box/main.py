from pathlib import Path
from cycax.cycad import Assembly, SheetMetal
from cycax.cycad.location import LEFT, RIGHT
from cycax.parts.fan import Fan80x80x25

def dial_a_box(working_directory, length=100, width=100, height=100):
    """Dial a box delivers custom boxes that is open at the top.

    All boxes are made from 100% 2mm thick unobtainium.
    """
    # Create the assembly
    assembly = Assembly("box")
    # Create the parts, the sides of the box, and add to assembly
    base_part = SheetMetal(part_no="base_part", x_size=length, y_size=width, z_size=2)
    assembly.add(base_part)
    left_part = SheetMetal(part_no="left_part", x_size=length, y_size=width-4, z_size=2)
    assembly.add(left_part)
    right_part = SheetMetal(part_no="right_part", x_size=length, y_size=width-4, z_size=2)
    assembly.add(right_part)
    front_part = SheetMetal(part_no="front_part", x_size=length-4, y_size=width-4, z_size=2)
    assembly.add(front_part)
    back_part = SheetMetal(part_no="back_part", x_size=length-4, y_size=width-4, z_size=2)
    assembly.add(back_part)

    # Rotate the parts
    right_part.rotate("y")
    left_part.rotate("y")
    front_part.rotate("yz")
    back_part.rotate("yz")
    
    # Position the parts
    right_part.level(top=base_part.bottom, front=base_part.front, right=base_part.right)
    left_part.level(top=base_part.bottom, front=base_part.front, left=base_part.left)
    front_part.level(top=base_part.bottom, front=base_part.front, left=left_part.right)
    back_part.level(top=base_part.bottom, back=base_part.back, right=right_part.left)

    # Save and render the part
    assembly.save(working_directory)
    assembly.render()
    assembly.render(engine='blender')

if __name__ == "__main__":
    working_directory = Path(__file__).parent.resolve() # Define where we want the artifacts to be stored
    dial_a_box(working_directory)
