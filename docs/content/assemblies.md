<!--
SPDX-FileCopyrightText: 2025 Tsolo.io

SPDX-License-Identifier: Apache-2.0
-->

# Assemblies Guide

Assemblies are collections of parts that work together to create complex objects. This guide covers creating, organizing, and managing assemblies in CyCAx.

## Basic Assembly Creation

Create an assembly by combining multiple parts:

```python
from cycax.cycad import Assembly, Print3D, SheetMetal

class MountingBracket(Print3D):
    def __init__(self):
        super().__init__(part_no="bracket", x_size=50, y_size=20, z_size=30)

class BasePanel(SheetMetal):
    def __init__(self):
        super().__init__(part_no="base", x_size=150, y_size=100, z_size=3)

# Create the assembly
assembly = Assembly("bracket_assembly")

# Create parts
base = BasePanel()
bracket_left = MountingBracket()
bracket_right = MountingBracket()

# Add parts to assembly
assembly.add(base, "base")
assembly.add(bracket_left, "left_bracket")
assembly.add(bracket_right, "right_bracket")
```

## Part Positioning

Use the `level()` method to position parts relative to each other:

```python
# Position left bracket
bracket_left.level(
    bottom=base.top,    # Bracket sits on base
    left=base.left,     # Align to left edge
    front=base.front    # Align to front edge
)
bracket_left.move(x=20, y=10)  # Fine-tune position

# Position right bracket
bracket_right.level(
    bottom=base.top,    # Bracket sits on base
    right=base.right,   # Align to right edge
    front=base.front    # Align to front edge
)
bracket_right.move(x=-20, y=10)  # Fine-tune position

# Save and render
assembly.save()
assembly.render()
```

## Assembly Sides and Features

Assemblies have six sides just like parts, allowing you to add features that affect multiple parts:

```python
class EnclosureAssembly(Assembly):
    def __init__(self):
        super().__init__("enclosure")
        
        # Create parts
        self.bottom = EnclosureBottom()
        self.top = EnclosureTop()
        
        # Add to assembly
        self.add(self.bottom, "bottom")
        self.add(self.top, "top")
        
        # Position parts
        self.top.level(bottom=self.bottom.top)
        
    def add_assembly_features(self):
        """Add features that span multiple parts."""
        # Add mounting holes that go through both parts
        hole_positions = [(25, 25), (125, 25), (25, 75), (125, 75)]
        
        for pos in hole_positions:
            # Holes through entire assembly height
            self.bottom.hole(pos=pos, diameter=4, external_subtract=True)
            self.top.hole(pos=pos, diameter=4, external_subtract=True)
```

## Nested Assemblies

Create complex hierarchies by nesting assemblies within other assemblies:

```python
class MotorMount(Assembly):
    def __init__(self):
        super().__init__("motor_mount")
        
        bracket = MountingBracket()
        motor = StepperMotor()  # Assuming this part exists
        
        self.add(bracket, "bracket")
        self.add(motor, "motor")
        
        motor.level(front=bracket.back)

class RobotArm(Assembly):
    def __init__(self):
        super().__init__("robot_arm")
        
        base = BaseJoint()
        shoulder = ShoulderJoint()
        elbow = ElbowJoint()
        
        # Add sub-assemblies
        motor_mount_base = MotorMount()
        motor_mount_shoulder = MotorMount()
        
        self.add(base, "base")
        self.add_assembly(motor_mount_base, "base_motor")
        self.add(shoulder, "shoulder")
        self.add_assembly(motor_mount_shoulder, "shoulder_motor")
        self.add(elbow, "elbow")
```

## Assembly Definition Pattern

Use the definition pattern for complex assemblies:

```python
class ComplexAssembly(Assembly):
    def __init__(self, name):
        super().__init__(name)
    
    def definition(self):
        """Define the assembly structure."""
        # Create all parts
        self.create_parts()
        
        # Position all parts
        self.position_parts()
        
        # Add assembly-level features
        self.add_features()
    
    def create_parts(self):
        """Create and add all parts to the assembly."""
        self.base = BasePanel(200, 150)
        self.cover = CoverPanel(200, 150)
        self.brackets = [MountingBracket() for _ in range(4)]
        
        self.add(self.base, "base")
        self.add(self.cover, "cover")
        for i, bracket in enumerate(self.brackets):
            self.add(bracket, f"bracket_{i}")
    
    def position_parts(self):
        """Position all parts relative to each other."""
        # Position cover above base
        self.cover.level(bottom=self.base.top)
        self.cover.move(z=50)  # 50mm separation
        
        # Position brackets in corners
        positions = [
            (20, 20), (180, 20), (20, 130), (180, 130)
        ]
        
        for bracket, pos in zip(self.brackets, positions):
            bracket.rotate("xz")  # Stand up
            bracket.level(bottom=self.base.top, left=self.base.left, front=self.base.front)
            bracket.move(x=pos[0], y=pos[1])
    
    def add_features(self):
        """Add features that span multiple parts."""
        # Through holes for assembly bolts
        for bracket in self.brackets:
            # Hole through base at bracket location
            x = bracket.location.x + bracket.x_size/2
            y = bracket.location.y + bracket.y_size/2
            self.base.top.hole(pos=(x, y), diameter=6, external_subtract=True)

# Usage
assembly = ComplexAssembly("my_complex_assembly")
assembly.definition()
assembly.save()
assembly.render()
```

## Assembly Transformations

Transform entire assemblies as units:

```python
# Rotate the entire assembly
assembly.rotate("z")  # Rotate 90° around Z axis

# Move the entire assembly
assembly.move(x=100, y=50, z=20)

# Level assembly relative to another assembly
assembly.level(bottom=other_assembly.top)
```

## Part Interactions

### Subtract Operations

Use parts to create negative space in other parts:

```python
class EnclosureWithCutouts(Assembly):
    def definition(self):
        enclosure = Enclosure()
        connector = USBConnector()  # Part representing USB connector
        
        self.add(enclosure, "enclosure")
        self.add(connector, "usb_connector", external_subtract=True)
        
        # Position connector to create cutout
        connector.level(
            right=enclosure.left,  # Connector extends from left side
            bottom=enclosure.bottom,
            front=enclosure.front
        )
        connector.move(z=15, y=20)  # Position at correct height
```

### Boolean Operations

Combine parts with different boolean operations:

```python
class BooleanAssembly(Assembly):
    def definition(self):
        main_body = MainPart()
        reinforcement = ReinforcementPart()
        cutout = CutoutPart()
        
        # Add main body
        self.add(main_body, "body")
        
        # Add reinforcement (union operation)
        self.add(reinforcement, "reinforcement", external_subtract=False)
        
        # Subtract cutout
        self.add(cutout, "cutout", external_subtract=True)
        
        # Position parts
        reinforcement.level(bottom=main_body.top)
        cutout.level(center=main_body.center)  # Center the cutout
```

## Assembly Organization

### Parts Management

Track and manage parts within assemblies:

```python
class OrganizedAssembly(Assembly):
    def __init__(self):
        super().__init__("organized")
        self.structural_parts = []
        self.fasteners = []
        self.electronics = []
    
    def add_structural_part(self, part, name):
        """Add a structural part with categorization."""
        self.add(part, name)
        self.structural_parts.append((name, part))
    
    def add_fastener(self, part, name):
        """Add a fastener with categorization."""
        self.add(part, name)
        self.fasteners.append((name, part))
    
    def get_parts_list(self):
        """Generate a parts list for manufacturing."""
        parts_list = {
            "Structural Parts": len(self.structural_parts),
            "Fasteners": len(self.fasteners),
            "Electronics": len(self.electronics),
            "Total Parts": len(self.parts)
        }
        return parts_list
```

### Assembly Validation

Validate assembly correctness:

```python
class ValidatedAssembly(Assembly):
    def validate(self):
        """Validate assembly for common issues."""
        issues = []
        
        # Check for overlapping parts
        for name1, part1 in self.parts.items():
            for name2, part2 in self.parts.items():
                if name1 != name2:
                    if self.parts_overlap(part1, part2):
                        issues.append(f"Parts {name1} and {name2} overlap")
        
        # Check for floating parts
        for name, part in self.parts.items():
            if not self.part_is_connected(part):
                issues.append(f"Part {name} is not connected to other parts")
        
        return issues
    
    def parts_overlap(self, part1, part2):
        """Check if two parts overlap in space."""
        # Implementation depends on CAD engine capabilities
        return False
    
    def part_is_connected(self, part):
        """Check if part is connected to the assembly."""
        # Implementation depends on design requirements
        return True
```

## Multi-Engine Assemblies

Use different CAD engines for different parts within the same assembly:

```python
class MultiEngineAssembly(Assembly):
    def definition(self):
        # Parametric part - best with OpenSCAD
        gear = ParametricGear(teeth=24, module=2)
        gear.render(engine="openscad")
        
        # Precision part - best with build123d
        bearing = PrecisionBearing()
        bearing.render(engine="build123d")
        
        # Complex surface - best with FreeCAD
        housing = ComplexHousing()
        housing.render(engine="freecad")
        
        self.add(gear, "gear")
        self.add(bearing, "bearing")
        self.add(housing, "housing")
        
        # Position parts
        bearing.level(center=gear.center)
        housing.level(bottom=gear.bottom)
        housing.move(z=-10)
```

## Assembly Export and Manufacturing

### Separate Parts for Manufacturing

Export parts individually for manufacturing:

```python
def export_for_manufacturing(assembly, output_dir):
    """Export assembly parts for different manufacturing processes."""
    
    # 3D printed parts
    print_parts_dir = output_dir / "3d_printed"
    print_parts_dir.mkdir(exist_ok=True)
    
    # Sheet metal parts  
    sheet_parts_dir = output_dir / "sheet_metal"
    sheet_parts_dir.mkdir(exist_ok=True)
    
    for name, part in assembly.parts.items():
        if isinstance(part, Print3D):
            part.save(print_parts_dir / name)
            part.render(engine="openscad")  # STL for 3D printing
            
        elif isinstance(part, SheetMetal):
            part.save(sheet_parts_dir / name)
            part.render(engine="build123d", format="dxf")  # DXF for laser cutting

# Usage
from pathlib import Path
assembly = ComplexAssembly("production_assembly")
assembly.definition()
export_for_manufacturing(assembly, Path("./manufacturing_output"))
```

### Assembly Instructions

Generate assembly documentation:

```python
def generate_assembly_instructions(assembly):
    """Generate step-by-step assembly instructions."""
    instructions = []
    
    # Sort parts by assembly order (base parts first)
    assembly_order = assembly.get_assembly_order()
    
    for step, (name, part) in enumerate(assembly_order, 1):
        instruction = f"Step {step}: Install {name}"
        
        # Add positioning information
        if hasattr(part, 'level_references'):
            refs = part.level_references
            instruction += f" - Position relative to {refs}"
        
        # Add fastener information
        if hasattr(part, 'fasteners'):
            instruction += f" - Secure with {len(part.fasteners)} fasteners"
            
        instructions.append(instruction)
    
    return instructions
```

## Performance Optimization

### Lazy Loading

Load parts only when needed for large assemblies:

```python
class LazyAssembly(Assembly):
    def __init__(self):
        super().__init__("lazy")
        self._part_definitions = {}
        self._loaded_parts = set()
    
    def define_part(self, name, part_class, *args, **kwargs):
        """Define a part without creating it."""
        self._part_definitions[name] = (part_class, args, kwargs)
    
    def get_part(self, name):
        """Load part on demand."""
        if name not in self._loaded_parts:
            part_class, args, kwargs = self._part_definitions[name]
            part = part_class(*args, **kwargs)
            self.add(part, name)
            self._loaded_parts.add(name)
        
        return self.parts[name]

# Usage
lazy = LazyAssembly()
lazy.define_part("heavy_part", ComplexPart, size=100, detail_level=10)
# Part is not created until accessed
part = lazy.get_part("heavy_part")  # Now it's created
```

## Next Steps

- **[Examples](examples.md)**: See complex assembly examples
- **[Integrations](integrations.md)**: Choose the right CAD engines for your assemblies
- **[Parts Guide](parts.md)**: Advanced part creation for assemblies

## API Reference

::: cycax.cycad.assembly
    options:
      show_submodules: true
