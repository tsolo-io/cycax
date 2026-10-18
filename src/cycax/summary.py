# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""`summary.json`: the measurements of a part (task python/05).

Measured from the exact model (STEP) with OCCT: volume, area, bounding box, centre of mass and
the mass from the material density (cycax/24). For sheet metal also the thickness, the flat
area (volume / thickness, exact for a constant thickness) and the list of bends from the spec.
The python worker writes it to the cache as `<name>-python-standard.json`; a local build123d
build writes the same file.

Units: mm, mm², mm³, g, g/cm³, degrees.
"""

from pathlib import Path

from cycax.materials import Material
from cycax.testing import measure

SUMMARY_VERSION = 1


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def sheet_metal_summary(spec: dict, volume_mm3: float) -> dict | None:
    bends = [f for f in spec.get("features", []) if f.get("type") == "bend"]
    if not bends:
        return None
    thickness = float(bends[0].get("thickness") or spec["features"][0].get("z_size"))
    return {
        "thickness_mm": thickness,
        "flat_area_mm2": _round(volume_mm3 / thickness, 2),
        "bend_count": len(bends),
        "bends": [
            {
                "id": bend.get("id"),
                "label": bend.get("label"),
                "angle_deg": bend.get("angle"),
                "direction": bend.get("direction"),
                "radius_mm": bend.get("radius"),
                "k_factor": bend.get("k_factor"),
                "length_mm": bend.get("width"),
                "parent": bend.get("parent"),
            }
            for bend in bends
        ],
    }


def make_summary(spec: dict, step_file: Path, *, engine: str, cache_hash: str = "") -> dict:
    """The summary of one part from its spec and its STEP file."""
    measured = measure(step_file)
    summary = {
        "summary_version": SUMMARY_VERSION,
        "name": spec["name"],
        "hash": cache_hash,
        "source": {"file": Path(step_file).name, "engine": engine},
        "volume_mm3": _round(measured.volume, 3),
        "area_mm2": _round(measured.area, 3),
        "bbox_mm": {
            "min": [_round(v) for v in measured.bbox_min],
            "max": [_round(v) for v in measured.bbox_max],
            "size": [_round(v) for v in measured.size],
        },
        "center_of_mass_mm": [_round(v) for v in measured.center],
        "solids": measured.solids,
    }
    material_meta = spec.get("meta", {}).get("material")
    if material_meta:
        material = Material.from_meta(material_meta)
        summary["material"] = material.to_meta()
        if material.density:
            summary["density_g_cm3"] = material.density
            summary["mass_g"] = _round(material.mass_g(measured.volume), 3)
    sheet_metal = sheet_metal_summary(spec, measured.volume)
    if sheet_metal:
        summary["sheet_metal"] = sheet_metal
    return summary
