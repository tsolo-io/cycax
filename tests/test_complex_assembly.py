
from pathlib import Path
from cycax.cycad.assembly import Assembly
from cycax.cycad.complex_assembly import ComplexAssembly
from cycax.cycad.cuboid import Cuboid, Print3D, SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d
from cycax.cycad.location import BACK, BOTTOM, FRONT, LEFT, RIGHT, SIDES, TOP
print("test")
def test_complex_assembly(tmp_path):
    part = SheetMetal(part_no = "this", x_size = 20, y_size = 10)
    part_2 = SheetMetal(part_no = "that", x_size = 30, y_size = 40)

    assembly1 = Assembly(name = "a")
    assembly2 = Assembly(name = "b")
    assembly1.add(part)
    assembly2.add(part_2)
    ca = ComplexAssembly(name = "ab")
    ca.add(assembly1)
    assembly2.at(x=50, y=50)
    ca.add(assembly2)
    assembly = ca.combine_assemblies()
    assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d()])
    assert False
