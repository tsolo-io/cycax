# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""How a part is made (task cycax/25). The same pattern as materials (cycax.materials).

A manufacturing object records the process, the machine, the settings, the quantity and the
human instructions. It goes into the spec `meta.manufacture` (not hashed: a new printer does
not change the part). Reports show the process and the instructions; machine outputs (slicer,
CNC tool paths) come later.

    from cycax.manufacture import FdmPrint
    from cycax.materials import PLA

    clip = Print3D(part_no="clip", x_size=20, y_size=10, z_size=5,
                   manufacture=FdmPrint(printer="Prusa MK4", filament="red PLA", layer=0.2, infill=20))

Defaults: `Print3D` -> `FdmPrint()`, `SheetMetal` -> `LaserCut()`, `SheetMetalBend` ->
`LaserCutAndBend()`. Other parts have no manufacturing information unless you give it.
"""

from dataclasses import dataclass, field


@dataclass
class Manufacture:
    """One manufacturing step, or a list of steps.

    Attributes:
        process: e.g. "3d-print", "laser-cut", "bend", "cnc-mill".
        machine: The machine, e.g. "Prusa MK4", "Shapeoko 4".
        settings: Process settings (shown in reports; used by machine outputs later).
        quantity: How many to make.
        instructions: Human instructions. Empty = made from the other fields.
        steps: The steps, in order, of a part that needs more than one process.
    """

    process: str = ""
    machine: str = ""
    settings: dict = field(default_factory=dict)
    quantity: int = 1
    instructions: str = ""
    steps: list["Manufacture"] = field(default_factory=list)

    def describe(self, material=None) -> str:
        """One sentence for a person. Subclasses make a better sentence from their fields."""
        words = [self.process.replace("-", " ").capitalize() or "Make"]
        if self.machine:
            words.append(f"on the {self.machine}")
        if material is not None:
            words.append(f"from {material.name}{' ' + material.grade if material.grade else ''}")
        return " ".join(words) + "."

    def human_instructions(self, material=None) -> list[str]:
        """The instructions, one line per step."""
        if self.steps:
            return [line for step in self.steps for line in step.human_instructions(material)]
        return [self.instructions or self.describe(material)]

    def to_meta(self, material=None) -> dict:
        """The spec `meta.manufacture` object."""
        meta: dict = {"process": self.process}
        if self.machine:
            meta["machine"] = self.machine
        if self.settings:
            meta["settings"] = dict(self.settings)
        meta["quantity"] = self.quantity
        if self.steps:
            meta["steps"] = [step.to_meta(material) for step in self.steps]
        meta["instructions"] = self.human_instructions(material)
        return meta


@dataclass
class FdmPrint(Manufacture):
    """3D print (fused filament)."""

    printer: str = ""
    filament: str = ""  # e.g. "red PLA"; empty = the part material
    layer: float = 0.2  # mm
    infill: int = 20  # percent
    supports: bool = False

    def __post_init__(self):
        self.process = self.process or "3d-print"
        self.machine = self.machine or self.printer
        self.settings = {
            "layer_mm": self.layer,
            "infill_percent": self.infill,
            "supports": self.supports,
        } | self.settings

    def describe(self, material=None) -> str:
        filament = self.filament or (material.name if material is not None else "")
        text = "3D print"
        if filament:
            text += f" with {filament} filament"
        if self.machine:
            text += f" on the {self.machine}"
        text += f", layer {self.layer:g} mm, infill {self.infill} %"
        text += ", with supports" if self.supports else ", no supports"
        return text + "."


@dataclass
class LaserCut(Manufacture):
    """Cut a flat sheet with a laser (or plasma/water jet: set `process`)."""

    def __post_init__(self):
        self.process = self.process or "laser-cut"

    def describe(self, material=None) -> str:
        text = "Laser cut"
        if material is not None:
            text += f" from {material.name}{' ' + material.grade if material.grade else ''} sheet"
        if self.machine:
            text += f" on the {self.machine}"
        return text + ". Remove the burrs."


@dataclass
class Bend(Manufacture):
    """Bend a sheet on a press brake."""

    def __post_init__(self):
        self.process = self.process or "bend"

    def describe(self, material=None) -> str:  # noqa: ARG002 - same signature
        text = "Bend in the order of the bend list"
        if self.machine:
            text += f" on the {self.machine}"
        return text + "."


def LaserCutAndBend(machine_cut: str = "", machine_bend: str = "", quantity: int = 1) -> Manufacture:  # noqa: N802 - reads as a class
    """Laser cut the flat pattern, then bend it (the default of SheetMetalBend)."""
    return Manufacture(
        process="laser-cut-and-bend",
        quantity=quantity,
        steps=[LaserCut(machine=machine_cut), Bend(machine=machine_bend)],
    )


@dataclass
class CncMill(Manufacture):
    """Mill on a CNC router. Several tools with tool changes (e.g. inside features, then the
    outside cut). Machine outputs come later; now only the instructions."""

    stock: str = ""  # e.g. "6 mm aluminium plate"
    tools: list[str] = field(default_factory=list)  # e.g. ["3 mm flat end mill", "6 mm flat end mill"]

    def __post_init__(self):
        self.process = self.process or "cnc-mill"
        if self.tools:
            self.settings = {"tools": list(self.tools)} | self.settings
        if self.stock:
            self.settings = {"stock": self.stock} | self.settings

    def describe(self, material=None) -> str:
        stock = self.stock or (material.name if material is not None else "")
        text = "Mill"
        if stock:
            text += f" from {stock}"
        if self.machine:
            text += f" on the {self.machine}"
        if self.tools:
            text += f" with {', then '.join(self.tools)}"
        return text + "."


def as_manufacture(value) -> Manufacture | None:
    if value is None or isinstance(value, Manufacture):
        return value
    msg = f"Not a manufacturing object: {value!r}. Use cycax.manufacture (FdmPrint, LaserCut, ...)."
    raise TypeError(msg)
