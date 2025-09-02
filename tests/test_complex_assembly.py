from cycax.cycad.assembly import Assembly
from cycax.cycad.cuboid import SheetMetal
from cycax.cycad.engines.assembly_build123d import AssemblyBuild123d
from cycax.cycad.engines.part_build123d import PartEngineBuild123d


def test_complex_assembly(tmp_path):
    part_1 = SheetMetal(part_no="this", x_size=20, y_size=10)
    part_1.bottom.hole(pos=(7, 7), diameter=3.2)
    part_1.bottom.hole(pos=(7, 7), diameter=3.2, external_subtract=True)
    part_2 = SheetMetal(part_no="that", x_size=30, y_size=40)
    part_2.top.hole(pos=(19, 19), diameter=3.2)
    part_2.top.hole(pos=(19, 19), diameter=3.2, external_subtract=True)

    part_3 = SheetMetal(part_no="this1", x_size=5, y_size=5)

    part_4 = SheetMetal(part_no="that1", x_size=3, y_size=3)

    assembly1 = Assembly(name="a")
    assembly2 = Assembly(name="b")
    assembly1.add(part_1)
    assembly2.add(part_2)
    assembly1.add(part_3)
    assembly2.add(part_4)
    part_3.level(bottom=part_1.top)
    part_4.level(right=part_2.left)
    assembly1.add(assembly2)
    # assembly2.at(x=50, y=50)
    assembly1.rotate_freeze_left()
    assembly1.rotate("x")
    assembly1.rotate_freeze_front()
    assembly1.rotate_freeze_top()
    assembly1.back.level(assembly2.back)
    assembly1.right.level(assembly2.left)
    # ca.level(assembly1, "BOTTOM", assembly2, "TOP")
    # ca.subtract(assembly2, "TOP", assembly1)
    # ca.level(assembly1, "RIGHT", assembly2, "LEFT")
    # ca.level(assembly1, "BACK", assembly2, "FRONT")
    assembly = assembly1.combine_all_assemblies()
    assembly.save(tmp_path / assembly.name)
    assembly.build(engine=AssemblyBuild123d(assembly.name), part_engines=[PartEngineBuild123d()])
