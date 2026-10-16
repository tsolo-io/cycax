# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# Tests for the @cycax_part / @cycax_assembly build target discovery.
import textwrap

import pytest

from cycax.cycad import Assembly, CycadPart
from cycax.targets import load_targets


def write(path, source):
    path.write_text(textwrap.dedent(source))
    return path


def test_function_and_class_targets(tmp_path):
    src = write(
        tmp_path / "things.py",
        """
        from cycax import Assembly, Print3D, cycax_assembly, cycax_part

        @cycax_part
        def cube():
            return Print3D(part_no="cube", x_size=10, y_size=10, z_size=10)

        @cycax_part(name="block")
        class Block(Print3D):
            def __init__(self):
                super().__init__(part_no="block", x_size=5, y_size=5, z_size=5)

        @cycax_part
        def pair():
            return [cube(), Block()]

        @cycax_assembly
        def stack():
            assembly = Assembly("stack")
            assembly.add(cube())
            return assembly

        def helper():
            return "not a target"
        """,
    )
    targets = {target.name: target for target in load_targets(src)}
    assert list(targets) == ["cube", "block", "pair", "stack"]
    assert targets["stack"].kind == "assembly"

    (cube,) = targets["cube"].make()
    assert isinstance(cube, CycadPart)
    assert cube.part_no == "cube"
    assert [part.part_no for part in targets["pair"].make()] == ["cube", "block"]
    (stack,) = targets["stack"].make()
    assert isinstance(stack, Assembly)


def test_select_by_name(tmp_path):
    src = write(
        tmp_path / "two.py",
        """
        from cycax import Print3D, cycax_part

        @cycax_part
        def one():
            return Print3D(part_no="one", x_size=1, y_size=1, z_size=1)

        @cycax_part
        def two():
            return Print3D(part_no="two", x_size=1, y_size=1, z_size=1)
        """,
    )
    assert [target.name for target in load_targets(src, "two")] == ["two"]
    with pytest.raises(LookupError, match="available targets: one, two"):
        load_targets(src, "three")


def test_imported_targets_are_not_collected(tmp_path):
    write(
        tmp_path / "library.py",
        """
        from cycax import Print3D, cycax_part

        @cycax_part
        def bolt():
            return Print3D(part_no="bolt", x_size=1, y_size=1, z_size=1)
        """,
    )
    # The sibling import also checks the file's directory is on sys.path while it is imported.
    src = write(
        tmp_path / "product.py",
        """
        from cycax import Assembly, cycax_assembly
        from library import bolt

        @cycax_assembly
        def product():
            assembly = Assembly("product")
            assembly.add(bolt())
            return assembly
        """,
    )
    assert [target.name for target in load_targets(src)] == ["product"]


def test_wrong_return_type(tmp_path):
    src = write(
        tmp_path / "wrong.py",
        """
        from cycax import Print3D, cycax_assembly

        @cycax_assembly
        def not_an_assembly():
            return Print3D(part_no="cube", x_size=1, y_size=1, z_size=1)
        """,
    )
    (target,) = load_targets(src)
    with pytest.raises(TypeError, match="returned Print3D, expected Assembly"):
        target.make()


def test_errors_propagate(tmp_path):
    src = write(
        tmp_path / "broken.py",
        """
        from cycax import cycax_part

        @cycax_part
        def broken():
            raise RuntimeError("boom")
        """,
    )
    (target,) = load_targets(src)
    with pytest.raises(RuntimeError, match="boom"):
        target.make()

    bad_import = write(tmp_path / "bad_import.py", "import does_not_exist\n")
    with pytest.raises(ModuleNotFoundError):
        load_targets(bad_import)


def test_module_path(tmp_path, monkeypatch):
    package = tmp_path / "mylib"
    package.mkdir()
    write(package / "__init__.py", "")
    write(
        package / "parts.py",
        """
        from cycax import Print3D, cycax_part

        @cycax_part
        def washer():
            return Print3D(part_no="washer", x_size=1, y_size=1, z_size=1)
        """,
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    assert [target.name for target in load_targets("mylib.parts")] == ["washer"]
