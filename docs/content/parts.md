<!--
SPDX-FileCopyrightText: 2025 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Parts Guide

Parts are the fundamental building blocks in CyCAx. This guide covers creating, customizing, and working with different types of parts.

## Part Types

CyCAx provides several built-in part types optimized for different manufacturing methods:

### Print3D Parts

Optimized for 3D printing with features like overhangs, support requirements, and layer considerations:

```python
from cycax.cycad import Print3D

class MyPrintedPart(Print3D):
    def __init__(self):
        super().__init__(
            part_no="my_printed_part",
            x_size=50,  # Width in mm
            y_size=30,  # Depth in mm  
            z_size=20   # Height in mm
        )
    
    def definition(self):
        """Define the part features."""
        # Add a hole through the front face
        self.front.hole(pos=(25, 15), diameter=8, depth=15)
        
        # Add countersink for screw head
        self.front.hole(pos=(25, 15), diameter=14, depth=3)
```

### SheetMetal Parts

For flat parts made from sheet materials (laser cutting, waterjet, CNC):

```python
from cycax.cycad import SheetMetal

class LaserCutBracket(SheetMetal):
    def __init__(self, thickness=3):
        super().__init__(
            part_no=f"bracket_t{thickness}",
            x_size=100,
            y_size=80,
            z_size=thickness
        )
        self.thickness = thickness
    
    def definition(self):
        # Mounting holes
        hole_positions = [(15, 15), (85, 15), (15, 65), (85, 65)]
        for pos in hole_positions:
            self.top.hole(pos=pos, diameter=6, external_subtract=True)
        
        # Weight reduction slots
        for x in [35, 50, 65]:
            self.top.hole(
                pos=(x, 40),
                width=8,
                height=30,
                external_subtract=True
            )
```

### Cuboid Parts

Basic geometric shapes for general use:

```python
from cycax.cycad import Cuboid

class BasicBlock(Cuboid):
    def __init__(self, size=25):
        super().__init__(
            part_no=f"block_{size}mm",
            x_size=size,
            y_size=size,
            z_size=size
        )
```

## Working with Part Sides

Every part has six sides that you can add features to:

```python
class PartWithFeatures(Print3D):
    def __init__(self):
        super().__init__(part_no="featured_part", x_size=40, y_size=30, z_size=20)
    
    def definition(self):
        # Front side (facing positive Y direction)
        self.front.hole(pos=(20, 10), diameter=8, depth=5)
        
        # Back side (facing negative Y direction)  
        self.back.hole(pos=(20, 10), diameter=6, depth=8)
        
        # Left side (facing negative X direction)
        self.left.hole(pos=(15, 10), diameter=4, external_subtract=True)
        
        # Right side (facing positive X direction)
        self.right.hole(pos=(15, 10), diameter=4, external_subtract=True)
        
        # Top side (facing positive Z direction)
        self.top.hole(pos=(20, 15), diameter=10, depth=3)
        
        # Bottom side (facing negative Z direction)
        self.bottom.hole(pos=(20, 15), diameter=5, external_subtract=True)
```

## Adding Features

### Holes

Different types of holes for various purposes:

```python
def definition(self):
    # Simple round hole
    self.front.hole(pos=(25, 15), diameter=8, depth=10)
    
    # Through hole (goes all the way through)
    self.front.hole(pos=(25, 15), diameter=5, external_subtract=True)
    
    # Rectangular hole/slot
    self.top.hole(pos=(30, 20), width=15, height=8, depth=5)
    
    # Countersink for screw heads
    self.front.hole(pos=(25, 15), diameter=3, depth=20)  # Pilot hole
    self.front.hole(pos=(25, 15), diameter=8, depth=3)   # Countersink
    
    # Counterbore for socket head screws
    self.top.hole(pos=(20, 20), diameter=4, external_subtract=True)  # Through hole
    self.top.hole(pos=(20, 20), diameter=8, depth=4)                 # Counterbore
```

### Positioning Features

Control exactly where features are placed:

```python
def definition(self):
    # Absolute positioning from part origin
    self.front.hole(pos=(10, 15), diameter=5, depth=8)
    
    # Use part dimensions for relative positioning
    center_x = self.x_size / 2
    center_y = self.z_size / 2  # Z for vertical on front face
    self.front.hole(pos=(center_x, center_y), diameter=8, depth=10)
    
    # Create patterns
    for i in range(3):
        x = 15 + (i * 10)  # Holes at x=15, 25, 35
        self.top.hole(pos=(x, 20), diameter=3, external_subtract=True)
```

## Parametric Parts

Create reusable parts that can be customized:

```python
class ParametricEnclosure(Print3D):
    def __init__(self, length=100, width=80, height=50, wall_thickness=3):
        super().__init__(
            part_no=f"enclosure_{length}x{width}x{height}_t{wall_thickness}",
            x_size=length,
            y_size=width,
            z_size=height
        )
        self.length = length
        self.width = width  
        self.height = height
        self.wall_thickness = wall_thickness
    
    def definition(self):
        # Hollow interior
        interior_length = self.length - (2 * self.wall_thickness)
        interior_width = self.width - (2 * self.wall_thickness)
        interior_height = self.height - self.wall_thickness
        
        self.top.hole(
            pos=(self.length/2, self.width/2),
            width=interior_length,
            height=interior_width,
            depth=interior_height
        )
        
        # Parametric ventilation holes
        num_holes_x = max(3, interior_length // 15)  # One hole every 15mm
        num_holes_y = max(2, interior_width // 20)   # One hole every 20mm
        
        for i in range(int(num_holes_x)):
            for j in range(int(num_holes_y)):
                x = self.wall_thickness + (i + 1) * (interior_length / (num_holes_x + 1))
                y = self.wall_thickness + (j + 1) * (interior_width / (num_holes_y + 1))
                
                self.front.hole(pos=(x, self.height - 10), diameter=3, depth=self.wall_thickness)

# Create different sizes
small_box = ParametricEnclosure(60, 40, 30, 2)
large_box = ParametricEnclosure(150, 100, 80, 4)
```

## Part Transformations

### Rotation

Rotate parts to different orientations:

```python
# Rotate around different axes
part.rotate("x")   # 90° around X axis
part.rotate("y")   # 90° around Y axis  
part.rotate("z")   # 90° around Z axis
part.rotate("xy")  # 90° around X, then Y
part.rotate("xyz") # 90° around X, Y, then Z
```

### Movement

Move parts to specific positions:

```python
# Move relative to current position
part.move(x=10, y=5, z=2)  # Move 10mm right, 5mm back, 2mm up

# Move to specific coordinates (used with level())
part.level(bottom=other_part.top)  # Position relative to another part
part.move(x=5)  # Then fine-tune position
```

### Leveling (Alignment)

Align parts relative to each other:

```python
# Align surfaces
bracket.level(
    bottom=base.top,     # Bracket bottom touches base top
    left=base.left,      # Align left edges
    front=base.front     # Align front edges
)

# More alignment options
bracket.level(
    right=base.right,    # Align right edges
    back=base.back,      # Align back edges
    top=base.top         # Align tops (same height)
)
```

## Advanced Part Features

### Custom Part Classes

Create your own specialized part types:

```python
class ElectronicsBracket(Print3D):
    """Specialized bracket for mounting electronic boards."""
    
    def __init__(self, board_width, board_length, standoff_height=5):
        # Add margins around the board
        super().__init__(
            part_no=f"pcb_bracket_{board_width}x{board_length}",
            x_size=board_width + 20,
            y_size=board_length + 20, 
            z_size=standoff_height + 3
        )
        self.board_width = board_width
        self.board_length = board_length
        self.standoff_height = standoff_height
    
    def add_mounting_holes(self, hole_positions):
        """Add PCB mounting holes at specified positions."""
        for pos in hole_positions:
            # Adjust position to account for margins
            adjusted_pos = (pos[0] + 10, pos[1] + 10)
            
            # Create standoff post
            self.top.hole(
                pos=adjusted_pos,
                diameter=6,  # Standoff outer diameter
                depth=self.standoff_height,
                external_subtract=False  # Positive feature
            )
            
            # Screw hole through standoff
            self.top.hole(
                pos=adjusted_pos,
                diameter=2.5,  # M2.5 screw clearance
                external_subtract=True
            )
    
    def definition(self):
        # Base mounting holes (for attaching bracket to enclosure)
        corner_inset = 5
        base_holes = [
            (corner_inset, corner_inset),
            (self.x_size - corner_inset, corner_inset),
            (corner_inset, self.y_size - corner_inset),
            (self.x_size - corner_inset, self.y_size - corner_inset)
        ]
        
        for pos in base_holes:
            self.bottom.hole(pos=pos, diameter=4, external_subtract=True)

# Usage
arduino_bracket = ElectronicsBracket(54, 68)  # Arduino Uno dimensions
arduino_mounting_holes = [(2.5, 15.2), (2.5, 66.0), (50.8, 15.2), (50.8, 66.0)]
arduino_bracket.add_mounting_holes(arduino_mounting_holes)
```

### Part Libraries

Organize reusable parts into libraries:

```python
# fasteners.py
class M3Screw(Cuboid):
    def __init__(self, length=20):
        super().__init__(
            part_no=f"m3_screw_{length}mm",
            x_size=3,
            y_size=3,
            z_size=length
        )

class M3Nut(Cuboid):
    def __init__(self):
        super().__init__(
            part_no="m3_nut",
            x_size=5.5,  # Hex nut width
            y_size=5.5,
            z_size=2.4   # Nut thickness
        )

# bearings.py  
class Bearing608(Cuboid):
    def __init__(self):
        super().__init__(
            part_no="bearing_608",
            x_size=22,  # Outer diameter
            y_size=22,
            z_size=7    # Thickness
        )
    
    def definition(self):
        # Outer ring
        self.top.hole(pos=(11, 11), diameter=22, depth=7, external_subtract=False)
        # Inner hole
        self.top.hole(pos=(11, 11), diameter=8, external_subtract=True)

# Use in your designs
from parts.fasteners import M3Screw, M3Nut
from parts.bearings import Bearing608
```

## Part Validation

Add validation to ensure parts meet requirements:

```python
class ValidatedBracket(Print3D):
    def __init__(self, length, height, thickness):
        if thickness < 2:
            raise ValueError("Thickness must be at least 2mm for 3D printing")
        if length < 20:
            raise ValueError("Length must be at least 20mm")
            
        super().__init__(
            part_no=f"validated_bracket_{length}x{height}x{thickness}",
            x_size=length,
            y_size=thickness,
            z_size=height
        )
        
        self.validate_geometry()
    
    def validate_geometry(self):
        """Validate part geometry for manufacturability."""
        aspect_ratio = self.z_size / self.y_size
        if aspect_ratio > 10:
            print(f"Warning: High aspect ratio ({aspect_ratio:.1f}) may cause printing issues")
```

## Next Steps

- **[Assemblies Guide](assemblies.md)**: Learn to combine parts into assemblies
- **[Examples](examples.md)**: See parts used in real projects  
- **[Integrations](integrations.md)**: Choose the right CAD engine for your parts

## API Reference

::: cycax.cycad.cycad_part
    options:
      show_submodules: true
