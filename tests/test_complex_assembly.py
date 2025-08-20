
from pathlib import Path
from cycax.cycad.assembly import Assembly
from cycax.cycad.complex_assembly import ComplexAssembly
from cycax.cycad.cuboid import Cuboid, Print3D, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP
print("test")
def test_complex_assembly(tmp_path):
    part_1 = SheetMetal(part_no = "this", x_size = 20, y_size = 10)
    part_1.bottom.hole(pos=(7,7), diameter=3.2)
    part_1.bottom.hole(pos=(7,7), diameter=3.2, external_subtract=True)
    part_2 = SheetMetal(part_no = "that", x_size = 30, y_size = 40)
    part_2.top.hole(pos=(19,19), diameter=3.2)
    part_2.top.hole(pos=(19,19), diameter=3.2, external_subtract=True)

    part_3 = SheetMetal(part_no = "this1", x_size = 5, y_size = 5)
    
    part_4 = SheetMetal(part_no = "that1", x_size = 3, y_size = 3)

    assembly1 = Assembly(name = "a")
    assembly2 = Assembly(name = "b")
    assembly1.add(part_1)
    assembly2.add(part_2)
    assembly1.add(part_3)
    assembly2.add(part_4)
    assembly1.level(part_3.bottom, part_1.top)
    assembly2.level(part_4.right, part_2.left)
    ca = ComplexAssembly(name = "ab")
    ca.add(assembly1)
    # assembly2.at(x=50, y=50)
    ca.add(assembly2)
    ca.rotate_freeze_left(assembly1)
    # ca.level(assembly1, "BOTTOM", assembly2, "TOP")
    # ca.subtract(assembly2, "TOP", assembly1)
    # ca.level(assembly1, "RIGHT", assembly2, "LEFT")
    # ca.level(assembly1, "BACK", assembly2, "FRONT")
    assembly = ca.combine_assemblies()
    assembly.save("/home/helen/src/tsolo/test-slot")
    assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d()])
    assert False
