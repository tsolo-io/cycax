<!--
SPDX-FileCopyrightText: 2025 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Examples and Tutorials

This page provides practical examples showing how to use CyCAx for real-world projects.

## Basic Examples

### Simple Enclosure

Create a 3D printable electronics enclosure:

```python
from cycax.cycad import Assembly, Print3D

class EnclosureBottom(Print3D):
    """Bottom half of an electronics enclosure."""
    
    def __init__(self, width=80, depth=60, height=15, wall_thickness=2):
        super().__init__(
            part_no=f"enclosure_bottom_{width}x{depth}x{height}",
            x_size=width,
            y_size=depth,
            z_size=height
        )
        self.width = width
        self.depth = depth
        self.height = height
        self.wall_thickness = wall_thickness
    
    def definition(self):
        # Create hollow interior
        interior_width = self.width - (2 * self.wall_thickness)
        interior_depth = self.depth - (2 * self.wall_thickness)
        
        self.top.hole(
            pos=(self.width/2, self.depth/2),
            width=interior_width,
            height=interior_depth,
            depth=self.height - self.wall_thickness
        )
        
        # Add mounting holes in corners
        hole_inset = 5
        positions = [
            (hole_inset, hole_inset),
            (self.width - hole_inset, hole_inset),
            (hole_inset, self.depth - hole_inset),
            (self.width - hole_inset, self.depth - hole_inset)
        ]
        
        for pos in positions:
            self.bottom.hole(
                pos=pos,
                diameter=3,
                external_subtract=True
            )

class EnclosureTop(Print3D):
    """Top half with ventilation holes."""
    
    def __init__(self, width=80, depth=60, height=8):
        super().__init__(
            part_no=f"enclosure_top_{width}x{depth}x{height}",
            x_size=width,
            y_size=depth,
            z_size=height
        )
        self.width = width
        self.depth = depth
    
    def definition(self):
        # Add ventilation grid
        for x in range(15, self.width - 10, 8):
            for y in range(15, self.depth - 10, 8):
                self.top.hole(
                    pos=(x, y),
                    diameter=2,
                    external_subtract=True
                )

# Create the complete enclosure
def create_enclosure(width=80, depth=60):
    enclosure = Assembly(f"enclosure_{width}x{depth}")
    
    bottom = EnclosureBottom(width, depth)
    top = EnclosureTop(width, depth)
    
    enclosure.add(bottom, "bottom")
    enclosure.add(top, "top")
    
    # Position top for 3D printing (separated)
    top.level(bottom=bottom.top, left=bottom.left, front=bottom.front)
    top.move(y=depth + 10)  # Separate by 10mm for printing
    
    return enclosure

# Usage
if __name__ == "__main__":
    enclosure = create_enclosure(100, 70)
    enclosure.save("./enclosure")
    enclosure.render()
```

### Parametric Bracket System

Create a reusable bracket system with different sizes:

```python
from cycax.cycad import Assembly, Print3D, SheetMetal

class MountingBracket(Print3D):
    """Parametric L-bracket for mounting devices."""
    
    def __init__(self, length=50, height=30, thickness=5, hole_diameter=4):
        super().__init__(
            part_no=f"bracket_{length}x{height}x{thickness}",
            x_size=length,
            y_size=thickness,
            z_size=height
        )
        self.length = length
        self.height = height
        self.thickness = thickness
        self.hole_diameter = hole_diameter
    
    def definition(self):
        # Add mounting holes along the length
        num_holes = max(2, self.length // 20)  # One hole every 20mm minimum
        hole_spacing = (self.length - 20) / (num_holes - 1) if num_holes > 1 else 0
        
        for i in range(num_holes):
            x = 10 + (i * hole_spacing)
            # Holes in the vertical face
            self.front.hole(
                pos=(x, self.height * 0.7),
                diameter=self.hole_diameter,
                external_subtract=True
            )
        
        # Add horizontal mounting holes
        self.bottom.hole(
            pos=(self.length/2, self.thickness/2),
            diameter=self.hole_diameter,
            external_subtract=True
        )

class BasePanel(SheetMetal):
    """Base mounting panel."""
    
    def __init__(self, width=200, depth=150, thickness=3):
        super().__init__(
            part_no=f"base_panel_{width}x{depth}x{thickness}",
            x_size=width,
            y_size=depth,
            z_size=thickness
        )
        self.width = width
        self.depth = depth

def create_bracket_assembly(panel_width=200, panel_depth=150, bracket_height=40):
    """Create an assembly with base panel and mounting brackets."""
    
    assembly = Assembly(f"bracket_system_{panel_width}x{panel_depth}")
    
    # Create base panel
    base = BasePanel(panel_width, panel_depth)
    assembly.add(base, "base")
    
    # Create brackets
    bracket_length = panel_depth - 40  # Leave 20mm margin on each side
    
    left_bracket = MountingBracket(bracket_length, bracket_height)
    right_bracket = MountingBracket(bracket_length, bracket_height)
    
    assembly.add(left_bracket, "left_bracket")
    assembly.add(right_bracket, "right_bracket")
    
    # Position brackets
    left_bracket.rotate("xz")  # Rotate to vertical position
    left_bracket.level(
        bottom=base.top,
        left=base.left,
        front=base.front
    )
    left_bracket.move(x=10, y=20)  # 10mm from edge, 20mm from front
    
    right_bracket.rotate("xz")
    right_bracket.level(
        bottom=base.top,
        right=base.right,
        front=base.front
    )
    right_bracket.move(x=-10, y=20)  # 10mm from edge, 20mm from front
    
    return assembly

# Create different sizes
if __name__ == "__main__":
    # Standard size
    standard = create_bracket_assembly(200, 150, 40)
    standard.save("./brackets/standard")
    standard.render()
    
    # Compact size
    compact = create_bracket_assembly(120, 100, 30)
    compact.save("./brackets/compact")
    compact.render()
```

## Advanced Examples

### Gear Factory

Create parametric gears with different specifications:

```python
from cycax.cycad import Print3D
import math

class Gear(Print3D):
    """Parametric gear with configurable teeth and dimensions."""
    
    def __init__(self, teeth=20, module=2, thickness=5, bore_diameter=6):
        # Calculate gear dimensions
        pitch_diameter = teeth * module
        outer_diameter = pitch_diameter + (2 * module)
        
        super().__init__(
            part_no=f"gear_T{teeth}_M{module}",
            x_size=outer_diameter,
            y_size=outer_diameter,
            z_size=thickness
        )
        
        self.teeth = teeth
        self.module = module
        self.thickness = thickness
        self.bore_diameter = bore_diameter
        self.pitch_diameter = pitch_diameter
        self.outer_diameter = outer_diameter
    
    def definition(self):
        # Add center bore
        self.top.hole(
            pos=(self.outer_diameter/2, self.outer_diameter/2),
            diameter=self.bore_diameter,
            external_subtract=True
        )
        
        # Add keyway if bore is large enough
        if self.bore_diameter >= 8:
            keyway_width = self.bore_diameter * 0.25
            keyway_length = self.bore_diameter * 0.8
            
            self.top.hole(
                pos=(self.outer_diameter/2, self.outer_diameter/2),
                width=keyway_width,
                height=keyway_length,
                external_subtract=True
            )

class GearTrain(Assembly):
    """Assembly of multiple gears in a gear train."""
    
    def __init__(self, gear_specs):
        super().__init__("gear_train")
        self.gear_specs = gear_specs
    
    def create_gear_train(self):
        previous_gear = None
        x_offset = 0
        
        for i, spec in enumerate(self.gear_specs):
            gear = Gear(**spec)
            gear_name = f"gear_{i+1}"
            self.add(gear, gear_name)
            
            if previous_gear is not None:
                # Calculate center distance
                center_distance = (previous_gear.pitch_diameter + gear.pitch_diameter) / 2
                x_offset += center_distance
                
                # Position gear
                gear.level(
                    bottom=previous_gear.bottom,
                    front=previous_gear.front
                )
                gear.move(x=x_offset)
            
            previous_gear = gear

# Create different gear trains
def create_reduction_gearbox():
    """Create a 3:1 reduction gear train."""
    gear_specs = [
        {"teeth": 30, "module": 2, "thickness": 8, "bore_diameter": 8},  # Driver
        {"teeth": 90, "module": 2, "thickness": 8, "bore_diameter": 10}  # Driven (3:1)
    ]
    
    train = GearTrain(gear_specs)
    train.create_gear_train()
    return train

if __name__ == "__main__":
    gearbox = create_reduction_gearbox()
    gearbox.save("./gears/reduction_3to1")
    gearbox.render()
```

### Modular Storage System

Create a stackable storage system:

```python
from cycax.cycad import Assembly, Print3D

class StorageBox(Print3D):
    """Modular stackable storage box."""
    
    def __init__(self, width=100, depth=80, height=60, wall_thickness=2):
        super().__init__(
            part_no=f"storage_box_{width}x{depth}x{height}",
            x_size=width,
            y_size=depth,
            z_size=height
        )
        self.width = width
        self.depth = depth
        self.height = height
        self.wall_thickness = wall_thickness
    
    def definition(self):
        # Create hollow interior
        interior_width = self.width - (2 * self.wall_thickness)
        interior_depth = self.depth - (2 * self.wall_thickness)
        interior_height = self.height - self.wall_thickness
        
        self.top.hole(
            pos=(self.width/2, self.depth/2),
            width=interior_width,
            height=interior_depth,
            depth=interior_height
        )
        
        # Add stacking features - posts on top
        post_inset = 10
        post_diameter = 8
        post_positions = [
            (post_inset, post_inset),
            (self.width - post_inset, post_inset),
            (post_inset, self.depth - post_inset),
            (self.width - post_inset, self.depth - post_inset)
        ]
        
        # Posts extend up from the top surface
        for pos in post_positions:
            # These would be positive features (posts) - implementation depends on CAD engine
            pass
        
        # Matching holes in the bottom for stacking
        for pos in post_positions:
            self.bottom.hole(
                pos=pos,
                diameter=post_diameter + 0.5,  # Clearance fit
                depth=8
            )
        
        # Add finger pull cutout
        self.front.hole(
            pos=(self.width/2, self.height - 10),
            width=40,
            height=8,
            depth=self.wall_thickness
        )
        
        # Add label area (recessed)
        self.front.hole(
            pos=(self.width/2, self.height/3),
            width=60,
            height=20,
            depth=0.5  # Shallow recess for label
        )

class StorageDivider(Print3D):
    """Removable divider for storage boxes."""
    
    def __init__(self, length, height, thickness=2):
        super().__init__(
            part_no=f"divider_{length}x{height}",
            x_size=length,
            y_size=thickness,
            z_size=height
        )
        self.length = length
        self.height = height
        self.thickness = thickness
    
    def definition(self):
        # Add finger pulls
        pull_width = 15
        pull_height = 8
        
        for x in [pull_width/2, self.length - pull_width/2]:
            self.front.hole(
                pos=(x, self.height - pull_height/2),
                width=pull_width,
                height=pull_height,
                depth=self.thickness
            )

def create_storage_system():
    """Create a complete modular storage system."""
    
    system = Assembly("modular_storage_system")
    
    # Create boxes of different sizes
    small_box = StorageBox(80, 60, 40)
    medium_box = StorageBox(120, 80, 50)
    large_box = StorageBox(160, 100, 60)
    
    system.add(small_box, "small_box")
    system.add(medium_box, "medium_box") 
    system.add(large_box, "large_box")
    
    # Arrange for printing (side by side)
    medium_box.level(bottom=small_box.bottom, left=small_box.right, front=small_box.front)
    medium_box.move(x=20)  # 20mm gap
    
    large_box.level(bottom=medium_box.bottom, left=medium_box.right, front=medium_box.front)
    large_box.move(x=20)  # 20mm gap
    
    # Add dividers for each box
    small_divider = StorageDivider(76, 38)  # Slightly smaller than interior
    medium_divider = StorageDivider(116, 48)
    large_divider = StorageDivider(156, 58)
    
    system.add(small_divider, "small_divider")
    system.add(medium_divider, "medium_divider")
    system.add(large_divider, "large_divider")
    
    # Position dividers below boxes
    small_divider.level(top=small_box.bottom, left=small_box.left, front=small_box.front)
    small_divider.move(z=-20)
    
    medium_divider.level(top=medium_box.bottom, left=medium_box.left, front=medium_box.front)
    medium_divider.move(z=-20)
    
    large_divider.level(top=large_box.bottom, left=large_box.left, front=large_box.front)
    large_divider.move(z=-20)
    
    return system

if __name__ == "__main__":
    storage = create_storage_system()
    storage.save("./storage_system")
    storage.render()
```

## Integration-Specific Examples

### OpenSCAD Advanced Features

```python
from cycax.cycad import Print3D

class ParametricEnclosure(Print3D):
    """Enclosure that showcases OpenSCAD's parametric capabilities."""
    
    def __init__(self, width=100, depth=80, height=50, corner_radius=5):
        super().__init__(
            part_no=f"param_enclosure_{width}x{depth}x{height}_r{corner_radius}",
            x_size=width,
            y_size=depth,
            z_size=height
        )
        self.corner_radius = corner_radius
    
    def definition(self):
        # OpenSCAD excels at parametric boolean operations
        # This would generate optimized OpenSCAD code for rounded corners
        pass

# Use OpenSCAD engine explicitly for best results
enclosure = ParametricEnclosure(120, 90, 60, 8)
enclosure.render(engine="openscad", engine_config={
    "resolution": 100,  # Higher resolution for smooth curves
    "optimize": True    # Enable OpenSCAD optimizations
})
```

### build123d Precision Parts

```python
from cycax.cycad import Print3D
from cycax.cycad.engines.part_build123d import PartEngineBuild123d

class PrecisionBearing(Print3D):
    """High-precision bearing that benefits from build123d's accuracy."""
    
    def __init__(self, outer_diameter=22, inner_diameter=8, thickness=7):
        super().__init__(
            part_no=f"bearing_OD{outer_diameter}_ID{inner_diameter}_T{thickness}",
            x_size=outer_diameter,
            y_size=outer_diameter,
            z_size=thickness
        )
        self.outer_diameter = outer_diameter
        self.inner_diameter = inner_diameter
    
    def definition(self):
        # Center bore
        self.top.hole(
            pos=(self.outer_diameter/2, self.outer_diameter/2),
            diameter=self.inner_diameter,
            external_subtract=True
        )

# Use build123d for high precision
bearing = PrecisionBearing(22, 8, 7)
bearing.render(engine="build123d", engine_config={
    "precision": 0.001,  # High precision
    "export_format": "step"  # Professional format
})
```

## Production Examples

### Electronics Project Box

Complete example for a real electronics project:

```python
from cycax.cycad import Assembly, Print3D

class RPiEnclosure(Print3D):
    """Raspberry Pi 4 enclosure with proper mounting and ventilation."""
    
    def __init__(self):
        # Raspberry Pi 4 dimensions: 85mm x 56mm
        super().__init__(
            part_no="rpi4_enclosure_bottom",
            x_size=100,  # 85mm + margins
            y_size=71,   # 56mm + margins  
            z_size=20
        )
    
    def definition(self):
        # Interior hollow
        self.top.hole(
            pos=(50, 35.5),
            width=90,
            height=61,
            depth=15
        )
        
        # Raspberry Pi mounting holes (official positions)
        mounting_holes = [
            (7.5, 7.5), (7.5, 63.5), (92.5, 7.5), (92.5, 63.5)
        ]
        
        for pos in mounting_holes:
            # Standoff posts for PCB mounting
            self.bottom.hole(pos=pos, diameter=6, depth=3)  # Standoff
            self.bottom.hole(pos=pos, diameter=2.5, external_subtract=True)  # Screw hole
        
        # Port cutouts
        # USB-C power (left side)
        self.left.hole(pos=(10, 12), width=12, height=6, external_subtract=True)
        
        # HDMI ports (right side)
        self.right.hole(pos=(15, 12), width=16, height=8, external_subtract=True)
        self.right.hole(pos=(35, 12), width=16, height=8, external_subtract=True)
        
        # USB-A ports (right side)
        self.right.hole(pos=(55, 12), width=15, height=7, external_subtract=True)
        self.right.hole(pos=(55, 4), width=15, height=7, external_subtract=True)
        
        # GPIO access (top)
        self.top.hole(pos=(25, 64), width=52, height=6, external_subtract=True)
        
        # SD card slot (front)
        self.front.hole(pos=(85, 8), width=18, height=3, external_subtract=True)

class RPiEnclosureTop(Print3D):
    """Top cover with ventilation."""
    
    def __init__(self):
        super().__init__(
            part_no="rpi4_enclosure_top",
            x_size=100,
            y_size=71,
            z_size=8
        )
    
    def definition(self):
        # Ventilation grid over CPU area
        cpu_x_center = 50  # Approximate CPU location
        cpu_y_center = 28
        
        # Grid of ventilation holes
        for x_offset in range(-15, 20, 5):
            for y_offset in range(-10, 15, 5):
                x = cpu_x_center + x_offset
                y = cpu_y_center + y_offset
                self.top.hole(
                    pos=(x, y),
                    diameter=2,
                    external_subtract=True
                )

# Create complete enclosure
def create_rpi_enclosure():
    enclosure = Assembly("raspberry_pi_4_enclosure")
    
    bottom = RPiEnclosure()
    top = RPiEnclosureTop()
    
    enclosure.add(bottom, "bottom")
    enclosure.add(top, "top")
    
    # Position top for printing (offset)
    top.level(bottom=bottom.bottom, left=bottom.left, front=bottom.front)
    top.move(y=80)  # Separate for printing
    
    return enclosure

if __name__ == "__main__":
    rpi_box = create_rpi_enclosure()
    rpi_box.save("./electronics/rpi4_enclosure")
    rpi_box.render()
    
    # Also create individual STL files
    bottom = RPiEnclosure()
    top = RPiEnclosureTop()
    
    bottom.save("./electronics/rpi4_bottom")
    top.save("./electronics/rpi4_top")
    
    bottom.render()
    top.render()
```

## Tips for Real Projects

### Organization
```python
# Organize complex projects with clear structure
project_root = Path("./my_project")
parts_dir = project_root / "parts"
assemblies_dir = project_root / "assemblies" 
outputs_dir = project_root / "outputs"

# Create directories
for dir_path in [parts_dir, assemblies_dir, outputs_dir]:
    dir_path.mkdir(parents=True, exist_ok=True)
```

### Version Control
```python
# Include version in part numbers for iteration tracking
class VersionedPart(Print3D):
    VERSION = "v1.2"
    
    def __init__(self):
        super().__init__(
            part_no=f"my_part_{self.VERSION}",
            x_size=50, y_size=30, z_size=20
        )
```

### Documentation
```python
def document_assembly(assembly):
    """Generate assembly documentation."""
    doc_path = f"./docs/{assembly.name}_README.md"
    with open(doc_path, "w") as f:
        f.write(f"# {assembly.name}\n\n")
        f.write(f"Parts count: {len(assembly.parts)}\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write("## Parts List:\n")
        for name, part in assembly.parts.items():
            f.write(f"- {name}: {part.part_no}\n")
```

These examples demonstrate the power and flexibility of CyCAx for creating everything from simple prototypes to production-ready designs. Start with the basic examples and gradually incorporate more advanced features as your projects grow in complexity.