# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Cross-engine test support (task cycax/22).

Engines must give the same result, so tests compare the output of one engine with the output
of another. The helpers here read the results back in a neutral way and measure them:

- `measure(path)`: volume, surface area, bounding box, centre of mass and number of solids of
  a STEP, BREP, FCStd, STL or GLB file. STEP/BREP/FCStd are exact (OCP); STL/GLB are meshes
  (numpy only, no extra dependency).
- `compare(a, b, ...)` / `assert_same(a, b, ...)`: the differences, with tolerances: tight for
  two exact shapes, profile-dependent for meshes.
- `check_golden(spec, name, folder)`: compare a compiled V2 spec with an approved copy;
  `CYCAX_UPDATE_GOLDEN=1` writes the approved copy.
- `assembly_instances(step_file)`: per instance in an assembly STEP: the name, 4x4 transform,
  centroid and world bounding box (used by the cross-engine assembly tests, cycax/40).

FCStd files are read without FreeCAD: an FCStd file is a zip with one BREP file per object.
The result is the shape of the object(s) that no other object uses.
"""

import json
import math
import os
import re
import struct
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from cycax.quality import PROFILE_SETTINGS
from cycax.spec import spec_hash

EXACT_FORMATS = {".step", ".stp", ".brep", ".brp", ".fcstd"}
MESH_FORMATS = {".stl", ".glb"}


@dataclass
class Measure:
    """Measured values of one model file (mm, mm², mm³)."""

    source: str
    exact: bool  # True for B-rep (STEP/BREP/FCStd), False for a mesh (STL/GLB)
    volume: float
    area: float
    bbox_min: tuple[float, float, float]
    bbox_max: tuple[float, float, float]
    center: tuple[float, float, float]  # centre of mass (uniform density)
    solids: int  # number of solids (exact) or of closed mesh shells is not known: -1
    extra: dict = field(default_factory=dict)

    @property
    def size(self) -> tuple[float, float, float]:
        return tuple(b - a for a, b in zip(self.bbox_min, self.bbox_max, strict=True))

    def to_dict(self) -> dict:
        return asdict(self)


# -- exact shapes -------------------------------------------------------------------------------
def _measure_shape(shape, source: str) -> Measure:
    import build123d

    if not isinstance(shape, build123d.Shape):
        shape = build123d.Compound(shape)
    solids = shape.solids()
    volume = sum(solid.volume for solid in solids)
    box = shape.bounding_box(optimal=True)
    if solids:
        # Volume-weighted centre of the solids (a compound gives the centre of all solids).
        weighted = [np.array(tuple(s.center(build123d.CenterOf.MASS))) * s.volume for s in solids]
        center = tuple(float(v) for v in (sum(weighted) / volume)) if volume else (0.0, 0.0, 0.0)
    else:
        center = tuple(shape.center(build123d.CenterOf.BOUNDING_BOX))
    return Measure(
        source=source,
        exact=True,
        volume=float(volume),
        area=float(sum(face.area for face in shape.faces())),
        bbox_min=(box.min.X, box.min.Y, box.min.Z),
        bbox_max=(box.max.X, box.max.Y, box.max.Z),
        center=tuple(float(v) for v in center),
        solids=len(solids),
    )


def _read_brep_bytes(data: bytes):
    import tempfile

    from OCP.BRep import BRep_Builder
    from OCP.BRepTools import BRepTools
    from OCP.TopoDS import TopoDS_Shape

    shape = TopoDS_Shape()
    with tempfile.NamedTemporaryFile(suffix=".brp") as handle:
        handle.write(data)
        handle.flush()
        BRepTools.Read_s(shape, handle.name, BRep_Builder())
    return shape


def _visible_objects(archive: zipfile.ZipFile) -> set[str]:
    """The objects with Visibility true in GuiDocument.xml (empty when there is no GUI data)."""
    if "GuiDocument.xml" not in archive.namelist():
        return set()
    gui = archive.read("GuiDocument.xml").decode("utf-8")
    visible = set()
    for match in re.finditer(r'<ViewProvider name="([^"]+)"(.*?)</ViewProvider>', gui, flags=re.S):
        flag = re.search(r'<Property name="Visibility"[^>]*>\s*<Bool value="(true|false)"', match.group(2))
        if flag and flag.group(1) == "true":
            visible.add(match.group(1))
    return visible


def fcstd_result_shapes(path: Path) -> dict[str, bytes]:
    """The BREP data of the result object(s) in an FCStd file: objects with a shape that no
    other object links to. Returns object name -> BREP bytes."""
    with zipfile.ZipFile(path) as archive:
        document = archive.read("Document.xml").decode("utf-8")
        names = archive.namelist()
        shapes: dict[str, str] = {}
        linked: set[str] = set()
        # <Object name="X"> ... <Property name="Shape" ...><Part file="PartShape3.brp"/>
        for match in re.finditer(r'<Object name="([^"]+)"[^>]*>(.*?)</Object>', document, flags=re.S):
            name, body = match.group(1), match.group(2)
            part = re.search(r'<Property name="Shape"[^>]*>\s*<Part\b[^>]*\bfile="([^"]+)"', body)
            if part and part.group(1) in names:
                shapes[name] = part.group(1)
            linked.update(re.findall(r'<Link\b[^>]*\bvalue="([^"]+)"', body))
            linked.update(re.findall(r'<LinkSub\b[^>]*\bvalue="([^"]+)"', body))
            linked.update(re.findall(r'<Link\b[^>]*\bobj="([^"]+)"', body))
        results = {name: file for name, file in shapes.items() if name not in linked}
        # Prefer what FreeCAD shows: a hidden object (e.g. the PartDesign Body under a fast
        # build's Result) is not the result.
        visible = _visible_objects(archive)
        if visible and any(name in visible for name in results):
            results = {name: file for name, file in results.items() if name in visible}
        if not results:
            results = shapes
        data = {name: archive.read(file) for name, file in results.items()}
    return {name: blob for name, blob in data.items() if blob.strip()}


def measure_exact(path: Path) -> Measure:
    import build123d

    suffix = path.suffix.lower()
    if suffix in {".step", ".stp"}:
        shape = build123d.import_step(path)
    elif suffix in {".brep", ".brp"}:
        shape = build123d.import_brep(path)
    else:  # .fcstd
        blobs = fcstd_result_shapes(path)
        if not blobs:
            msg = f"No shape found in {path}"
            raise ValueError(msg)
        shapes = [build123d.Compound(_read_brep_bytes(blob)) for blob in blobs.values()]
        shape = shapes[0] if len(shapes) == 1 else build123d.Compound(children=shapes)
        measured = _measure_shape(shape, str(path))
        measured.extra["objects"] = sorted(blobs)
        return measured
    return _measure_shape(shape, str(path))


# -- meshes -------------------------------------------------------------------------------------
def read_stl(path: Path) -> np.ndarray:
    """Triangles of an STL file (ASCII or binary) as an (n, 3, 3) array."""
    data = path.read_bytes()
    if len(data) >= 84:  # noqa: PLR2004 - binary header + count
        count = struct.unpack_from("<I", data, 80)[0]
        if 84 + count * 50 == len(data):
            record = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])
            return np.frombuffer(data, dtype=record, count=count, offset=84)["vertices"].astype(float)
    text = data.decode("ascii", errors="replace")
    numbers = re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", text)
    return np.array(numbers, dtype=float).reshape(-1, 3, 3)


_GLTF_TYPES = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}
_GLTF_SIZES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _node_matrix(node: dict) -> np.ndarray:
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4).T  # column-major
    t = node.get("translation", [0, 0, 0])
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    s = node.get("scale", [1, 1, 1])
    rotation = np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )
    matrix = np.eye(4)
    matrix[:3, :3] = rotation * np.array(s)
    matrix[:3, 3] = t
    return matrix


def read_glb(path: Path) -> np.ndarray:
    """Triangles of all meshes in a GLB file, in world coordinates, as an (n, 3, 3) array.

    glTF is Y-up and in metres (build123d and Blender write it so). The result is in mm and
    Z-up, as CyCAx uses: (x, y, z) glTF -> (x, -z, y) mm.
    """
    data = path.read_bytes()
    magic, _version, _length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:  # noqa: PLR2004 - "glTF"
        msg = f"{path} is not a GLB file"
        raise ValueError(msg)
    offset, gltf, binary = 12, None, b""
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        chunk = data[offset + 8 : offset + 8 + chunk_length]
        if chunk_type == 0x4E4F534A:  # noqa: PLR2004 - JSON
            gltf = json.loads(chunk)
        elif chunk_type == 0x004E4942:  # noqa: PLR2004 - BIN
            binary = chunk
        offset += 8 + chunk_length

    def accessor(index: int) -> np.ndarray:
        acc = gltf["accessors"][index]
        view = gltf["bufferViews"][acc["bufferView"]]
        start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        width = _GLTF_SIZES[acc["type"]]
        dtype = np.dtype(_GLTF_TYPES[acc["componentType"]])
        stride = view.get("byteStride", 0)
        if stride and stride != dtype.itemsize * width:
            rows = [
                np.frombuffer(binary, dtype=dtype, count=width, offset=start + i * stride) for i in range(acc["count"])
            ]
            return np.array(rows)
        return np.frombuffer(binary, dtype=dtype, count=acc["count"] * width, offset=start).reshape(-1, width)

    triangles = []

    def visit(node_index: int, parent: np.ndarray):
        node = gltf["nodes"][node_index]
        matrix = parent @ _node_matrix(node)
        if "mesh" in node:
            for primitive in gltf["meshes"][node["mesh"]]["primitives"]:
                if primitive.get("mode", 4) != 4:  # noqa: PLR2004 - triangles only
                    continue
                points = accessor(primitive["attributes"]["POSITION"]).astype(float)
                points = (np.c_[points, np.ones(len(points))] @ matrix.T)[:, :3]
                if "indices" in primitive:
                    indices = accessor(primitive["indices"]).astype(int).reshape(-1)
                else:
                    indices = np.arange(len(points))
                triangles.append(points[indices].reshape(-1, 3, 3))
        for child in node.get("children", []):
            visit(child, matrix)

    scene = gltf["scenes"][gltf.get("scene", 0)]
    for root in scene["nodes"]:
        visit(root, np.eye(4))
    if not triangles:
        return np.zeros((0, 3, 3))
    result = np.concatenate(triangles) * 1000.0  # glTF metres -> mm
    return result[:, :, [0, 2, 1]] * np.array([1, -1, 1])  # Y-up -> Z-up


def measure_triangles(triangles: np.ndarray, source: str) -> Measure:
    v0, v1, v2 = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    cross = np.cross(v1 - v0, v2 - v0)
    area = 0.5 * np.linalg.norm(cross, axis=1).sum()
    signed = np.einsum("ij,ij->i", v0, np.cross(v1, v2)) / 6.0  # tetrahedra to the origin
    volume = signed.sum()
    centroids = (v0 + v1 + v2) / 4.0  # tetrahedron centroid (4th vertex = origin)
    center = (centroids * signed[:, None]).sum(axis=0) / volume if volume else np.zeros(3)
    points = triangles.reshape(-1, 3)
    return Measure(
        source=source,
        exact=False,
        volume=float(abs(volume)),
        area=float(area),
        bbox_min=tuple(float(v) for v in points.min(axis=0)),
        bbox_max=tuple(float(v) for v in points.max(axis=0)),
        center=tuple(float(v) for v in center),
        solids=-1,
        extra={"triangles": len(triangles)},
    )


def measure(path: Path | str) -> Measure:
    """Measure a STEP, BREP, FCStd, STL or GLB file."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in EXACT_FORMATS:
        return measure_exact(path)
    if suffix == ".stl":
        return measure_triangles(read_stl(path), str(path))
    if suffix == ".glb":
        return measure_triangles(read_glb(path), str(path))
    msg = f"Cannot measure {path.suffix} files."
    raise ValueError(msg)


# -- comparing ----------------------------------------------------------------------------------
@dataclass
class Tolerance:
    length: float  # mm, for bounding box and centre
    volume: float  # relative
    area: float  # relative


# Two B-rep kernels agree to about 1e-5; 1e-4 still finds a 1 mm move (through the centre).
EXACT = Tolerance(length=1e-3, volume=1e-4, area=1e-4)


def tolerance_for(a: Measure, b: Measure, profile: str = "standard") -> Tolerance:
    """Tight for two exact shapes. With a mesh: the mesh deviation of the profile (the chord
    error of the tessellation), with a relative volume/area margin that grows with it."""
    if a.exact and b.exact:
        return EXACT
    deviation = PROFILE_SETTINGS["stl_linear_deflection_mm"][profile]
    angular = PROFILE_SETTINGS["stl_angular_deflection_rad"][profile]
    # A chord with angle a under-estimates a circle's area by about a^2 / 24 (relative).
    margin = max(1e-3, angular**2 / 12)
    # A mesh from a coarse tessellation can be smaller than the true shape by ~deviation.
    return Tolerance(length=max(deviation * 2, 1e-3), volume=margin, area=margin)


def compare(a: Measure, b: Measure, tolerance: Tolerance | None = None, *, profile: str = "standard") -> list[str]:
    """The differences between two measures that are larger than the tolerance (empty = same)."""
    tol = tolerance or tolerance_for(a, b, profile)
    problems = []

    def relative(name: str, x: float, y: float, limit: float):
        scale = max(abs(x), abs(y), 1e-9)
        if abs(x - y) / scale > limit:
            problems.append(f"{name}: {x:.6g} != {y:.6g} (difference {abs(x - y) / scale:.2e} > {limit:.1e})")

    relative("volume", a.volume, b.volume, tol.volume)
    relative("area", a.area, b.area, tol.area)
    for label, xs, ys in (("bbox min", a.bbox_min, b.bbox_min), ("bbox max", a.bbox_max, b.bbox_max)):
        for axis, x, y in zip("xyz", xs, ys, strict=True):
            if abs(x - y) > tol.length:
                problems.append(f"{label} {axis}: {x:.6g} != {y:.6g} (> {tol.length:g} mm)")
    # Tessellation moves the centre of mass much less than the bounding box, so its tolerance
    # is tighter: a moved hole changes the centre but not the box, volume or area.
    center_tol = max(tol.length / 4, 1e-3)
    for axis, x, y in zip("xyz", a.center, b.center, strict=True):
        if abs(x - y) > center_tol:
            problems.append(f"centre {axis}: {x:.6g} != {y:.6g} (> {center_tol:g} mm)")
    if a.exact and b.exact and a.solids != b.solids:
        problems.append(f"solids: {a.solids} != {b.solids}")
    return problems


def assert_same(a: Measure | Path | str, b: Measure | Path | str, tolerance: Tolerance | None = None, **kwargs):
    """Assert that two files (or measures) are the same model within the tolerance."""
    ma = a if isinstance(a, Measure) else measure(a)
    mb = b if isinstance(b, Measure) else measure(b)
    problems = compare(ma, mb, tolerance, **kwargs)
    if problems:
        raise AssertionError(f"{ma.source} != {mb.source}:\n  " + "\n  ".join(problems))  # noqa: S101 - test helper


# -- golden specs -------------------------------------------------------------------------------
def check_golden(spec: dict, name: str, folder: Path | str, *, update: bool | None = None):
    """Compare a compiled V2 spec with the approved copy `<folder>/<name>.json`.

    With `update` (default: the environment variable CYCAX_UPDATE_GOLDEN=1) or when there is no
    approved copy, the spec is written as the approved copy. The assertion message says if the
    geometry hash changed (a geometry change) or only the meta (description, colour, ...).
    """
    folder = Path(folder)
    file = folder / f"{name}.json"
    if update is None:
        update = os.environ.get("CYCAX_UPDATE_GOLDEN") == "1"
    if update or not file.exists():
        folder.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(spec, indent=2) + "\n")  # key order is part of the hash
        return
    approved = json.loads(file.read_text())
    if approved == json.loads(json.dumps(spec)):
        return
    old_hash, new_hash = spec_hash(approved), spec_hash(spec)
    what = (
        f"the geometry changed (hash {old_hash} -> {new_hash})"
        if old_hash != new_hash
        else "only the meta changed (same geometry hash)"
    )
    msg = f"Spec {name} is different from {file}: {what}. If this is correct, run with CYCAX_UPDATE_GOLDEN=1."
    raise AssertionError(msg)


# -- assemblies ---------------------------------------------------------------------------------
@dataclass
class Instance:
    name: str
    transform: list[list[float]]  # 4x4, row-major, mm
    center: tuple[float, float, float]
    bbox_min: tuple[float, float, float]
    bbox_max: tuple[float, float, float]
    volume: float
    hash: str | None = None


def assembly_instances(step_file: Path | str) -> list[Instance]:
    """One entry per leaf instance of an assembly STEP file (name from the STEP label)."""
    import build123d

    root = build123d.import_step(Path(step_file))
    found = []  # (instance shape, location of its parent in the world)

    def walk(shape, parent, depth=0):
        children = list(getattr(shape, "children", ()) or ())
        if not children:
            if shape.solids():
                found.append((shape, parent))
            return
        generic = (getattr(shape, "label", "") or "") in ("", "COMPOUND")
        if all(isinstance(child, build123d.Solid) for child in children) and not (depth == 0 or generic):
            found.append((shape, parent))  # a named compound that holds the solids of one part
            return
        for child in children:
            # An (sub)assembly: its children are placed with its location.
            walk(child, parent * shape.location, depth + 1)

    walk(root, build123d.Location())
    instances = []
    for shape, parent in found:
        measured = _measure_shape(shape.moved(parent), str(step_file))
        matrix = (parent * shape.location).wrapped.Transformation()
        transform = [[matrix.Value(r, c) for c in range(1, 5)] for r in range(1, 4)] + [[0.0, 0.0, 0.0, 1.0]]
        label = getattr(shape, "label", "") or ""
        name, _, part_hash = label.partition("#")  # `<instance>#<hash>` (cycax/39)
        instances.append(
            Instance(
                name=name,
                hash=part_hash or None,
                transform=transform,
                center=measured.center,
                bbox_min=measured.bbox_min,
                bbox_max=measured.bbox_max,
                volume=measured.volume,
            )
        )
    return instances


def close(a: float, b: float, tol: float = 1e-3) -> bool:
    return math.isclose(a, b, abs_tol=tol)


# -- cross-engine matrix (task cycax/23) --------------------------------------------------------
# What each engine is compared on: an exact format when it has one, else a mesh.
COMPARE_FORMAT = {"build123d": "step", "freecad": "step", "python": "step", "openscad": "stl"}


@dataclass
class CrossEngineResult:
    name: str
    measures: dict[str, Measure] = field(default_factory=dict)  # engine -> measure
    errors: dict[str, str] = field(default_factory=dict)  # engine -> build error
    pairs: dict[tuple[str, str], list[str]] = field(default_factory=dict)  # (a, b) -> problems

    @property
    def ok(self) -> bool:
        return not self.errors and all(not problems for problems in self.pairs.values())

    def report(self) -> str:
        lines = [f"{self.name}:"]
        lines += [f"  {engine}: build failed: {error.splitlines()[0]}" for engine, error in self.errors.items()]
        for (a, b), problems in self.pairs.items():
            lines.append(f"  {a} vs {b}: {'same' if not problems else 'DIFFERENT'}")
            lines += [f"      {problem}" for problem in problems]
        return "\n".join(lines)


class _FixedSpec:
    """A part object whose export() returns a given spec (used to plant a fault)."""

    def __init__(self, spec: dict):
        self._spec = spec

    def export(self) -> dict:
        return json.loads(json.dumps(self._spec))


def _pair_tolerance(a: str, b: str, ma: Measure, mb: Measure, profile: str) -> Tolerance:
    tol = tolerance_for(ma, mb, profile)
    if "openscad" in (a, b):
        # OpenSCAD makes circles from $fn segments: the chord error is size * (1 - cos(pi/fn)).
        fn = PROFILE_SETTINGS["openscad_fn"][profile]
        chord = 1 - math.cos(math.pi / fn)
        size = max(*ma.size, *mb.size)
        tol = Tolerance(
            length=max(tol.length, size * chord * 2),
            volume=max(tol.volume, 4 * chord),
            area=max(tol.area, 4 * chord),
        )
    return tol


def cross_engine(
    obj,
    engines: list[str],
    work: Path,
    *,
    backend: str = "local",
    profile: str = "standard",
    server_url: str | None = None,
    spec_hook=None,
) -> CrossEngineResult:
    """Build one part with each engine and compare all pairs.

    Each engine gets its own cache folder and `force`, so no engine reuses another engine's
    file. `spec_hook(engine, spec) -> spec` can change the spec for one engine (a planted
    fault, to test the test).
    """
    from cycax.app.builder import Builder, BuildItem  # noqa: PLC0415
    from cycax.app.project import Project, Settings  # noqa: PLC0415

    spec = obj.export()
    result = CrossEngineResult(spec["name"])
    for engine in engines:
        settings = Settings()
        settings.cache_folder = str(work / f"cache_{engine}")
        settings.backend = backend
        if server_url:
            settings.server_url = server_url
        project = Project(work / engine, settings)
        engine_spec = spec_hook(engine, json.loads(json.dumps(spec))) if spec_hook else spec
        item = BuildItem(f"{spec['name']}_{engine}", _FixedSpec(engine_spec), engine)
        fmt = COMPARE_FORMAT.get(engine, "step")
        built = Builder(project, outputs=[fmt], backend=backend, profile=profile, force=True).build([item])
        target = next(iter(built.targets.values()))
        if target.error or fmt not in target.files:
            result.errors[engine] = target.error or f"no {fmt} file"
            continue
        result.measures[engine] = measure(target.files[fmt])
    names = list(result.measures)
    for index, a in enumerate(names):
        for b in names[index + 1 :]:
            ma, mb = result.measures[a], result.measures[b]
            result.pairs[(a, b)] = compare(ma, mb, _pair_tolerance(a, b, ma, mb, profile))
    return result


@dataclass
class GlbNode:
    name: str
    transform: list[list[float]]  # 4 x 4 row-major, glTF units (metres)
    extras: dict


def glb_nodes(path: Path | str) -> list[GlbNode]:
    """The mesh nodes of a GLB with their name, world transform and extras (blender/07 read-back)."""
    data = Path(path).read_bytes()
    offset, gltf = 12, None
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        if chunk_type == 0x4E4F534A:  # noqa: PLR2004 - JSON
            gltf = json.loads(data[offset + 8 : offset + 8 + chunk_length])
        offset += 8 + chunk_length
    nodes = []

    def visit(index: int, parent: np.ndarray):
        node = gltf["nodes"][index]
        matrix = parent @ _node_matrix(node)
        if "mesh" in node:
            nodes.append(GlbNode(node.get("name", ""), matrix.tolist(), node.get("extras", {})))
        for child in node.get("children", []):
            visit(child, matrix)

    for root in gltf["scenes"][gltf.get("scene", 0)]["nodes"]:
        visit(root, np.eye(4))
    return nodes


# -- cross-engine assemblies (task cycax/40) -----------------------------------------------------
def glb_instances(path: Path | str) -> list[Instance]:
    """One entry per mesh node of a GLB (Blender assemblies): name, part hash (extras), world
    box, centre and volume of its mesh, in mm and Z-up like the STEP read-back."""
    data = Path(path).read_bytes()
    offset, gltf, binary = 12, None, b""
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        chunk = data[offset + 8 : offset + 8 + chunk_length]
        if chunk_type == 0x4E4F534A:  # noqa: PLR2004
            gltf = json.loads(chunk)
        elif chunk_type == 0x004E4942:  # noqa: PLR2004
            binary = chunk
        offset += 8 + chunk_length

    def accessor(index: int) -> np.ndarray:
        acc = gltf["accessors"][index]
        view = gltf["bufferViews"][acc["bufferView"]]
        start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        width = _GLTF_SIZES[acc["type"]]
        dtype = np.dtype(_GLTF_TYPES[acc["componentType"]])
        return np.frombuffer(binary, dtype=dtype, count=acc["count"] * width, offset=start).reshape(-1, width)

    instances = []

    def visit(index: int, parent: np.ndarray):
        node = gltf["nodes"][index]
        matrix = parent @ _node_matrix(node)
        if "mesh" in node:
            tris = []
            for primitive in gltf["meshes"][node["mesh"]]["primitives"]:
                points = accessor(primitive["attributes"]["POSITION"]).astype(float)
                points = (np.c_[points, np.ones(len(points))] @ matrix.T)[:, :3]
                indices = (
                    accessor(primitive["indices"]).astype(int).reshape(-1)
                    if "indices" in primitive
                    else np.arange(len(points))
                )
                tris.append(points[indices].reshape(-1, 3, 3))
            triangles = np.concatenate(tris) * 1000.0
            triangles = triangles[:, :, [0, 2, 1]] * np.array([1, -1, 1])
            measured = measure_triangles(triangles, str(path))
            extras = node.get("extras", {})
            instances.append(
                Instance(
                    name=extras.get("cycax_instance") or node.get("name", ""),
                    transform=matrix.tolist(),
                    center=measured.center,
                    bbox_min=measured.bbox_min,
                    bbox_max=measured.bbox_max,
                    volume=measured.volume,
                    hash=extras.get("cycax_hash"),
                )
            )
        for child in node.get("children", []):
            visit(child, matrix)

    for root in gltf["scenes"][gltf.get("scene", 0)]["nodes"]:
        visit(root, np.eye(4))
    return instances


def compare_instances(a: list[Instance], b: list[Instance], length: float = 1e-3) -> list[str]:
    """Instance by instance (by name): the same parts (hash), world boxes and centres."""
    problems = []
    by_a, by_b = {i.name: i for i in a}, {i.name: i for i in b}
    for name in sorted(set(by_a) ^ set(by_b)):
        problems.append(f"{name}: only in {'the first' if name in by_a else 'the second'}")
    for name in sorted(set(by_a) & set(by_b)):
        x, y = by_a[name], by_b[name]
        if x.hash and y.hash and x.hash != y.hash:
            problems.append(f"{name}: part {x.hash} != {y.hash}")
        for label, p, q in (("min", x.bbox_min, y.bbox_min), ("max", x.bbox_max, y.bbox_max)):
            for axis, u, v in zip("xyz", p, q, strict=True):
                if abs(u - v) > length:
                    problems.append(f"{name}: bbox {label} {axis} {u:.6g} != {v:.6g}")
        for axis, u, v in zip("xyz", x.center, y.center, strict=True):
            if abs(u - v) > max(length, 1e-3):
                problems.append(f"{name}: centre {axis} {u:.6g} != {v:.6g}")
    return problems


def interference(step_file: Path | str, tolerance: float = 1e-3) -> list[tuple[str, str, float]]:
    """Pairs of instances of an assembly STEP whose solids overlap (volume > tolerance mm³)."""
    import build123d  # noqa: PLC0415

    root = build123d.import_step(Path(step_file))
    leaves = []

    def walk(shape, parent):
        children = list(getattr(shape, "children", ()) or ())
        if children and not all(isinstance(c, build123d.Solid) for c in children):
            for child in children:
                walk(child, parent * shape.location)
        elif shape.solids():
            leaves.append((getattr(shape, "label", "") or "", shape.moved(parent)))

    walk(root, build123d.Location())
    clashes = []
    for i, (name_a, a) in enumerate(leaves):
        box_a = a.bounding_box()
        for name_b, b in leaves[i + 1 :]:
            box_b = b.bounding_box()
            lo_a, hi_a, lo_b, hi_b = tuple(box_a.min), tuple(box_a.max), tuple(box_b.min), tuple(box_b.max)
            if any(hi_a[k] <= lo_b[k] or hi_b[k] <= lo_a[k] for k in range(3)):
                continue
            common = a.intersect(b)
            volume = sum(s.volume for s in common.solids()) if common else 0.0
            if volume > tolerance:
                clashes.append((name_a.partition("#")[0], name_b.partition("#")[0], volume))
    return clashes


ASSEMBLY_OUTPUT = {"build123d": "step", "freecad": "step", "blender": "glb"}


def cross_engine_assembly(
    assembly, engines: list[str], work: Path, *, server_url: str | None = None, profile: str = "standard"
) -> CrossEngineResult:
    """Build one assembly with each engine and compare the instances of all pairs.

    Engines: "build123d" (local), "freecad" and "blender" (server, needs `server_url`)."""
    from cycax.app.builder import Builder, BuildItem  # noqa: PLC0415
    from cycax.app.project import Project, Settings  # noqa: PLC0415

    result = CrossEngineResult(assembly.name)
    read: dict[str, list[Instance]] = {}
    for engine in engines:
        settings = Settings()
        settings.cache_folder = str(work / f"cache_{engine}")
        backend = "local" if engine == "build123d" else "server"
        settings.backend = backend
        if server_url:
            settings.server_url = server_url
        fmt = ASSEMBLY_OUTPUT[engine]
        builder = Builder(Project(work / engine, settings), outputs=[fmt], backend=backend, profile=profile, force=True)
        built = builder.build_item(BuildItem(f"{assembly.name}_{engine}", assembly, engine))
        if built.error or fmt not in built.files:
            result.errors[engine] = built.error or f"no {fmt}"
            continue
        read[engine] = glb_instances(built.files[fmt]) if fmt == "glb" else assembly_instances(built.files[fmt])
    names = list(read)
    for index, a in enumerate(names):
        for b in names[index + 1 :]:
            mesh = "blender" in (a, b)
            length = max(PROFILE_SETTINGS["stl_linear_deflection_mm"][profile] * 2, 1e-3) if mesh else 1e-3
            result.pairs[(a, b)] = compare_instances(read[a], read[b], length)
    result.extra = read  # type: ignore[attr-defined]
    return result
