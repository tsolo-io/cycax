<!--
SPDX-FileCopyrightText: 2025 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Getting Started

This guide will walk you through creating your first CyCAx project step by step.

## Your First Part

Let's start by creating a simple 3D printable part:

```python
from cycax.cycad import Print3D

class SimpleCube(Print3D):
    def __init__(self):
        super().__init__(
            part_no="simple_cube",
            x_size=20,  # 20mm width
            y_size=20,  # 20mm depth  
            z_size=20   # 20mm height
        )

# Create and render the part
cube = SimpleCube()
cube.save()
cube.render()
```

This creates a 20x20x20mm cube optimized for 3D printing and generates the necessary files.

## Adding Features to Parts

Let's make the cube more interesting by adding holes:

```python
from cycax.cycad import Print3D

class CubeWithHoles(Print3D):
    def __init__(self):
        super().__init__(
            part_no="cube_with_holes",
            x_size=30,
            y_size=30,
            z_size=20
        )
    
    def definition(self):
        """Define the part features."""
        # Add a 10mm deep hole to front face
        self.front.hole(
            pos=(15, 10),      # Center of the face
            diameter=5,        # 5mm diameter
            depth=10           # 10mm deep
        )
        
        # Add holes through the top face
        for x in [10, 20]:
            for y in [10, 20]:
                self.top.hole(
                    pos=(x, y),
                    diameter=3
                )

# Create and render
part = CubeWithHoles()
part.save()
part.render()
```

## Creating Your First Assembly

Now let's combine multiple parts into an assembly:

```python
from cycax.cycad import Assembly, Print3D, SheetMetal

class Base(SheetMetal):
    def __init__(self):
        super().__init__(
            part_no="base_plate",
            x_size=100,
            y_size=60,
            z_size=3  # 3mm thick sheet
        )

class Bracket(Print3D):
    def __init__(self):
        super().__init__(
            part_no="bracket",
            x_size=20,
            y_size=50,
            z_size=30
        )
    
    def definition(self):
        # Add mounting holes
        self.bottom.hole(pos=(10, 10), diameter=4.0)
        self.bottom.hole(pos=(10, 10), diameter=4.2, external_subtract=True)
        self.bottom.hole(pos=(10, 40), diameter=4.0)
        self.bottom.hole(pos=(10, 40), diameter=4.2, external_subtract=True)

# Create the assembly
assembly = Assembly("simple_assembly")

# Create parts
base = Base()
bracket_left = Bracket()
bracket_right = Bracket()

# Add parts to assembly
assembly.add(base, "base")
assembly.add(bracket_left, "bracket_left")
assembly.add(bracket_right, "bracket_right")

# Position the brackets
bracket_left.level(
    bottom=base.top,    # Bracket sits on top of base
    left=base.left,     # Align to left edge
    front=base.front,   # Align to front edge
    subtract=True       # Subtract the parts features, marked as external_subtract, from the leveled part
)

bracket_right.level(
    bottom=base.top,    # Bracket sits on top of base
    right=base.right,   # Align to right edge
    front=base.front,   # Align to front edge
    subtract=True       # Subtract the parts features, marked as external_subtract, from the leveled part
)

# Save and render
assembly.save()
assembly.render()
```

## Understanding Part Types

CyCAx provides several part types optimized for different manufacturing methods:

### Print3D
For 3D printed parts with features optimized for additive manufacturing:

```python
from cycax.cycad import Print3D

class PrintedPart(Print3D):
    def __init__(self):
        super().__init__(part_no="printed_part", x_size=30, y_size=20, z_size=15)
```

### SheetMetal  
For flat parts made from sheet material (laser cutting, CNC):

```python
from cycax.cycad import SheetMetal

class LaserCutPart(SheetMetal):
    def __init__(self):
        super().__init__(part_no="laser_part", x_size=50, y_size=50, z_size=3)
```

### Cuboid
Basic geometric shapes:

```python
from cycax.cycad import Cuboid

class BasicShape(Cuboid):
    def __init__(self):
        super().__init__(part_no="basic", x_size=25, y_size=25, z_size=10)
```

## Working with Sides

Every part has six sides that you can add features to:

```python
class PartWithFeatures(Print3D):
    def __init__(self):
        super().__init__(part_no="featured_part", x_size=40, y_size=30, z_size=20)
    
    def definition(self):
        # Front side features
        self.front.hole(pos=(20, 10), diameter=8, depth=5)
        
        # Top side features
        self.top.hole(pos=(20, 15), diameter=4)  # Through the top out the bottom
        
        # Left side features
        self.left.hole(pos=(15, 10), diameter=6, depth=8)
```

## Positioning and Alignment

Use the `level()` method to position parts relative to each other:

```python
# Align part2 to part1
part2.level(
    bottom=part1.top,    # part2's bottom touches part1's top
    left=part1.left,     # Align left edges
    front=part1.front    # Align front edges
)

# Move parts with offset
part2.move(x=10, y=5, z=2)  # Move 10mm right, 5mm back, 2mm up
```

## Choosing Rendering Engines

CyCAx supports multiple CAD engines. Choose based on your needs:

```python
# Render with different engines
part.render()                    # Default (usually OpenSCAD)
part.render(engine="openscad")   # Explicit OpenSCAD
part.render(engine="build123d")  # build123d for modern Python CAD
part.render(engine="freecad")    # FreeCAD for advanced features
```

## Complete Example: Enclosure

Here's a complete example that creates a simple electronic enclosure:

```python
from cycax.cycad import Assembly, Print3D

class EnclosureBottom(Print3D):
    def __init__(self):
        super().__init__(
            part_no="enclosure_bottom",
            x_size=80,
            y_size=60, 
            z_size=15
        )
    
    def definition(self):
        # Hollow out the inside
        self.top.box(
            pos=(40, 30),  # Center
            width=70,      # Inner width
            height=50,     # Inner height
            depth=10       # Hollow depth
        )
        
        # Mounting holes in corners
        for x in (10, 70):
            for y in (10, 50):
                self.bottom.hole(
                    pos=(x, y),
                    diameter=3.0
                )
                self.bottom.hole(
                    pos=(x, y),
                    diameter=3.2,
                    external_subtract=True
                )

class EnclosureTop(Print3D):
    def __init__(self):
        super().__init__(
            part_no="enclosure_top",
            x_size=80,
            y_size=60,
            z_size=5
        )

# Create the assembly
enclosure = Assembly("electronic_enclosure")

bottom = EnclosureBottom()
top = EnclosureTop()

enclosure.add(bottom, "bottom")
enclosure.add(top, "top")

# Position top above bottom
top.level(bottom=bottom.top, left=bottom.left, front=bottom.front)
top.move(z=20)  # Separate for printing

# Generate files
enclosure.save("./enclosure_output")
enclosure.render()
print(f"Enclosure files saved to: ./enclosure_output/{enclosure.name}")
```

## Next Steps

Now that you understand the basics:

1. **[Parts Guide](parts.md)**: Learn advanced part creation techniques
2. **[Assemblies Guide](assemblies.md)**: Master complex assembly creation
3. **[Examples](examples.md)**: Study real-world examples
4. **[Integrations](integrations.md)**: Set up different CAD engines

## Common Patterns

### Parametric Parts
```python
class ParametricBracket(Print3D):
    def __init__(self, length=50, width=20, thickness=5):
        super().__init__(
            part_no=f"bracket_{length}x{width}x{thickness}",
            x_size=length,
            y_size=width,
            z_size=thickness
        )
        self.length = length
        self.width = width
        self.thickness = thickness
    
    def definition(self):
        # Features based on parameters
        hole_spacing = self.length / 3
        for i in range(3):
            x = hole_spacing * (i + 0.5)
            self.top.hole(pos=(x, self.width/2), diameter=4)
            self.top.hole(pos=(x, self.width/2), diameter=4, external_subtract=True)
```

### Reusable Components
```python
def create_mounting_holes(part, positions, diameter=4):
    """Add mounting holes to any part."""
    for pos in positions:
        part.bottom.hole(pos=pos, diameter=diameter)
        part.bottom.hole(pos=pos, diameter=diameter, external_subtract=True)

# Use with any part
bracket = Bracket()
create_mounting_holes(bracket, [(10, 10), (40, 10), (25, 30)])
```
