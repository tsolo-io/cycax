# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: E501 - the page template and the viewer script have long lines
"""The HTML report: a quick view of one part or assembly (task cycax/27).

The workers (or the local engines) make the artifacts; this module only writes the report
files into one folder (default `build/<target>/report/`):

    index.html      the page (images, sizes, mass, material, manufacturing, tables)
    summary.json    the measurements (cycax.summary)
    views.svg       the six side views (light report)
    render.png      a render, when an engine that makes PNG was available
    model.glb/.stl  the 3D model for the viewer
    features.csv    every feature with its label (the same labels as in the views)
    holes.csv       the holes: label, side, position, diameter, depth
    bom.csv         assemblies: the bill of materials

The page works offline, except the 3D viewer: it loads three.js from a CDN when it can, and
says so when it cannot. There is no PDF report.
"""

import base64
import csv
import html
import io
import json
import shutil
from collections import Counter
from pathlib import Path

from cycax.report import units
from cycax.report.light import SIDES, features_csv, items_of, side_view_svg
from cycax.spec import spec_hash

VIEWER_FORMATS = ("glb", "stl")
EMBED_LIMIT = 15_000_000  # bytes; larger models are loaded from the file (needs a web server)


def holes_csv(spec: dict) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["label", "side", "x", "y", "z", "diameter", "depth"])
    for item in items_of(spec)[1:]:
        feature = item.feature
        if item.role == "cut" and feature.get("type") == "cylinder" and "diameter" in feature:
            writer.writerow(
                [
                    item.label,
                    feature.get("side", ""),
                    _num(feature["x"]),
                    _num(feature["y"]),
                    _num(feature["z"]),
                    _num(feature["diameter"]),
                    _num(feature.get("depth", "")),
                ]
            )
    return out.getvalue()


def bom_rows(assembly_spec: dict, part_specs: dict[str, dict], summaries: dict[str, dict]) -> list[dict]:
    """One row per unique part (by hash) of an assembly spec."""
    counts = Counter(part["hash"] for part in assembly_spec["parts"])
    rows = []
    seen = set()
    for part in assembly_spec["parts"]:
        part_hash = part["hash"]
        if part_hash in seen:
            continue
        seen.add(part_hash)
        spec = part_specs.get(part_hash, {})
        meta = spec.get("meta", {})
        material = meta.get("material", {})
        summary = summaries.get(part_hash, {})
        mass = summary.get("mass_g")
        rows.append(
            {
                "part": part["name"],
                "quantity": counts[part_hash],
                "material": " ".join(v for v in (material.get("name", ""), material.get("code", "")) if v),
                "process": meta.get("manufacture", {}).get("process", ""),
                "mass_g": mass if mass is not None else "",
                "total_mass_g": round(mass * counts[part_hash], 3) if mass is not None else "",
                "hash": part_hash,
            }
        )
    return rows


def bom_csv(rows: list[dict]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(
        out, fieldnames=["part", "quantity", "material", "process", "mass_g", "total_mass_g", "hash"]
    )
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def _num(value) -> str:
    return f"{value:g}" if isinstance(value, int | float) else str(value)


def _table(rows: list[list[str]], header: list[str]) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in header)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def _csv_rows(text: str) -> tuple[list[str], list[list[str]]]:
    rows = list(csv.reader(io.StringIO(text)))
    return (rows[0], rows[1:]) if rows else ([], [])


def render_index(
    spec: dict,
    *,
    target: str,
    summary: dict | None,
    files: dict[str, str],
    tables: dict[str, str],
    bom: list[dict] | None = None,
) -> str:
    """The report page. `files`: role -> file name in the report folder."""
    meta = spec.get("meta", {})
    name = spec["name"]
    title = html.escape(target if target == name else f"{target} ({name})")
    parts = [
        f"<h1>{title}</h1>",
        f'<p class="muted">{html.escape(spec["kind"])} · spec version '
        f"{spec.get('spec_version')} · hash <code>{html.escape(spec_hash(spec))}</code></p>",
    ]
    if meta.get("description"):
        parts.append("".join(f"<p>{html.escape(p)}</p>" for p in meta["description"].split("\n\n")))
    if meta.get("notes"):
        parts.append(f'<div class="notes"><pre>{html.escape(meta["notes"])}</pre></div>')

    facts = []
    if summary:
        size = summary["bbox_mm"]["size"]
        facts.append(("Size", " x ".join(f"{v:g}" for v in size) + " mm"))
        facts.append(("Volume", units.volume(summary["volume_mm3"])))
        facts.append(("Surface area", units.area(summary["area_mm2"])))
        if "mass_g" in summary:
            facts.append(("Mass", units.mass(summary["mass_g"])))
        facts.append(("Centre of mass", ", ".join(f"{v:g}" for v in summary["center_of_mass_mm"]) + " mm"))
        sheet = summary.get("sheet_metal")
        if sheet:
            facts.append(("Sheet thickness", f"{sheet['thickness_mm']:g} mm"))
            facts.append(("Flat area", f"{sheet['flat_area_mm2']:.4g} mm²"))
            facts.append(("Bends", str(sheet["bend_count"])))
    material = meta.get("material")
    if material:
        facts.append(
            (
                "Material",
                " ".join(v for v in (material.get("name"), material.get("code"), material.get("standard")) if v),
            )
        )
    if bom is not None:
        masses = [row["total_mass_g"] for row in bom if row["total_mass_g"] != ""]
        facts.append(("Parts", f"{sum(row['quantity'] for row in bom)} ({len(bom)} different)"))
        if masses:
            facts.append(("Mass of the known parts", units.mass(sum(masses))))
    if facts:
        parts.append(
            "<dl>" + "".join(f"<dt>{html.escape(k)}</dt><dd>{html.escape(v)}</dd>" for k, v in facts) + "</dl>"
        )

    manufacture = meta.get("manufacture")
    if manufacture:
        steps = "".join(f"<li>{html.escape(line)}</li>" for line in manufacture.get("instructions", []))
        parts.append(
            f"<h2>How to make it</h2><p>Process: <strong>{html.escape(manufacture.get('process', ''))}</strong>"
            f" · quantity {manufacture.get('quantity', 1)}</p><ol>{steps}</ol>"
        )

    images = []
    if "render" in files:
        images.append(f'<figure><img src="{files["render"]}" alt="Render"><figcaption>Render</figcaption></figure>')
    if "drawing" in files:
        images.append(
            f'<figure class="wide"><img src="{files["drawing"]}" alt="Drawing"><figcaption>Drawing</figcaption></figure>'
        )
    if "views" in files:
        images.append(
            f'<figure class="wide"><img src="{files["views"]}" alt="Side views">'
            "<figcaption>Side views: cuts red and dashed, adds green, bend lines blue</figcaption></figure>"
        )
    if images:
        parts.append('<h2>Pictures</h2><div class="images">' + "".join(images) + "</div>")
    if "model" in files:
        parts.append(
            f'<h2>3D view</h2><div id="viewer" data-model="{files["model"]}"><p class="muted" id="viewer-status">'
            "Loading the 3D viewer (it needs internet for three.js)...</p></div>"
        )

    if bom:
        header = ["part", "quantity", "material", "process", "mass_g", "total_mass_g"]
        parts.append("<h2>Bill of materials</h2>" + _table([[row[h] for h in header] for row in bom], header))
    for title_text, key in (("Holes", "holes"), ("Features", "features")):
        if tables.get(key):
            header, rows = _csv_rows(tables[key])
            if rows:
                parts.append(f"<h2>{title_text}</h2>" + _table(rows, header))

    links = "".join(f'<li><a href="{html.escape(f)}">{html.escape(f)}</a></li>' for f in sorted(set(files.values())))
    parts.append(f"<h2>Files</h2><ul>{links}</ul>")
    return PAGE.format(title=title, body="\n".join(parts), viewer=VIEWER_SCRIPT if "model" in files else "")


def write_html_report(
    folder: Path,
    spec: dict,
    *,
    target: str,
    artifacts: dict[str, Path],
    part_specs: dict[str, dict] | None = None,
    part_summaries: dict[str, dict] | None = None,
) -> Path:
    """Write the report folder. `artifacts`: format -> file (summary, svg, png, glb, stl, step)."""
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    files: dict[str, str] = {}
    summary = None
    if "summary" in artifacts:
        summary = json.loads(Path(artifacts["summary"]).read_text())
        shutil.copyfile(artifacts["summary"], folder / "summary.json")
        files["summary"] = "summary.json"
    for role, fmt, target_name in (
        ("views", "svg", "views.svg"),
        ("render", "png", "render.png"),
        ("drawing", "drawing", "drawing.svg"),
    ):
        if fmt in artifacts:
            shutil.copyfile(artifacts[fmt], folder / target_name)
            files[role] = target_name
    model_data = None
    for fmt in VIEWER_FORMATS:
        if fmt in artifacts:
            shutil.copyfile(artifacts[fmt], folder / f"model.{fmt}")
            files["model"] = f"model.{fmt}"
            # Browsers do not let a file:// page fetch a file next to it; a data URL works.
            data = Path(artifacts[fmt]).read_bytes()
            if len(data) <= EMBED_LIMIT:
                model_data = f"data:application/octet-stream;base64,{base64.b64encode(data).decode()}"
            break
    if "step" in artifacts:
        shutil.copyfile(artifacts["step"], folder / f"{spec['name']}.step")
        files["step"] = f"{spec['name']}.step"
    tables = {}
    bom = None
    if spec["kind"] == "part":
        items = items_of(spec)
        for view in SIDES:  # fills the "views" column of the feature table
            side_view_svg(spec, view, items)
        tables = {"features": features_csv(items), "holes": holes_csv(spec)}
        for key, text in tables.items():
            (folder / f"{key}.csv").write_text(text)
            files[key] = f"{key}.csv"
    else:
        bom = bom_rows(spec, part_specs or {}, part_summaries or {})
        (folder / "bom.csv").write_text(bom_csv(bom))
        files["bom"] = "bom.csv"
    index = folder / "index.html"
    page = render_index(spec, target=target, summary=summary, files=files, tables=tables, bom=bom)
    if model_data:
        page = page.replace(
            f'data-model="{files["model"]}"', f'data-model="{model_data}" data-type="{files["model"][-3:]}"'
        )
    index.write_text(page)
    return index


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - CyCAx report</title>
<style>
:root {{ --fg: #1a1a1a; --muted: #6b6b6b; --line: #ddd; --bg: #fff; --panel: #f6f6f6; --accent: #0b5fff; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --fg: #e8e8e8; --muted: #9a9a9a; --line: #3a3a3a; --bg: #161616; --panel: #222; --accent: #6ea0ff; }}
  .images img {{ background: #fff; }}
}}
body {{ font-family: system-ui, sans-serif; color: var(--fg); background: var(--bg); margin: 0 auto;
  max-width: 72rem; padding: 1.5rem 1rem 3rem; line-height: 1.45; }}
a {{ color: var(--accent); }}
.muted {{ color: var(--muted); }}
code {{ background: var(--panel); padding: 0.1rem 0.3rem; border-radius: 3px; }}
dl {{ display: grid; grid-template-columns: max-content 1fr; gap: 0.3rem 1.2rem; }}
dt {{ color: var(--muted); }} dd {{ margin: 0; }}
.images {{ display: flex; flex-wrap: wrap; gap: 1rem; }}
.images figure {{ margin: 0; flex: 1 1 18rem; max-width: 26rem; }}
.images figure.wide {{ max-width: 46rem; flex-basis: 30rem; }}
.images img {{ width: 100%; height: auto; border: 1px solid var(--line); border-radius: 4px; }}
figcaption {{ color: var(--muted); font-size: 0.85rem; }}
table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; display: block; overflow-x: auto; }}
th, td {{ text-align: left; padding: 0.3rem 0.6rem; border-bottom: 1px solid var(--line); white-space: nowrap; }}
#viewer {{ height: 28rem; background: var(--panel); border: 1px solid var(--line); border-radius: 4px; position: relative; }}
#viewer p {{ position: absolute; margin: 0.5rem; }}
.notes pre {{ white-space: pre-wrap; font-family: inherit; }}
</style>
</head>
<body>
{body}
<p class="muted">Made by CyCAx. The values are from the CAD model; check them before you order.</p>
{viewer}
</body>
</html>
"""

VIEWER_SCRIPT = """<script type="importmap">
{"imports": {"three": "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js",
             "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/"}}
</script>
<script type="module">
const box = document.getElementById("viewer");
const status = document.getElementById("viewer-status");
const file = box.dataset.model;
const kind = box.dataset.type || file.split(".").pop();
try {
  const THREE = await import("three");
  const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
  const { STLLoader } = await import("three/addons/loaders/STLLoader.js");
  const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xeaeaea);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 2.2));
  const light = new THREE.DirectionalLight(0xffffff, 1.2);
  light.position.set(1, 2, 3);
  scene.add(light);
  const camera = new THREE.PerspectiveCamera(45, box.clientWidth / box.clientHeight, 0.1, 1e6);
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(box.clientWidth, box.clientHeight);
  box.appendChild(renderer.domElement);
  const controls = new OrbitControls(camera, renderer.domElement);
  function show(object) {
    scene.add(object);
    const bounds = new THREE.Box3().setFromObject(object);
    const size = bounds.getSize(new THREE.Vector3()).length() || 1;
    const centre = bounds.getCenter(new THREE.Vector3());
    camera.position.copy(centre).add(new THREE.Vector3(size, size * 0.7, size));
    camera.near = size / 1000; camera.far = size * 100; camera.updateProjectionMatrix();
    controls.target.copy(centre); controls.update();
    status.textContent = "";
  }
  if (kind === "glb") {
    new GLTFLoader().load(file, (gltf) => show(gltf.scene), undefined, () => { status.textContent = "Cannot load " + file + " (open the page through a web server, or use the files above)."; });
  } else {
    new STLLoader().load(file, (geometry) => {
      geometry.computeVertexNormals();
      const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0x6f93c9, roughness: 0.6 }));
      mesh.rotation.x = -Math.PI / 2;
      show(mesh);
    }, undefined, () => { status.textContent = "Cannot load " + file + "."; });
  }
  (function animate() { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); })();
  new ResizeObserver(() => { camera.aspect = box.clientWidth / box.clientHeight; camera.updateProjectionMatrix();
    renderer.setSize(box.clientWidth, box.clientHeight); }).observe(box);
} catch (error) {
  status.textContent = "The 3D viewer needs internet (three.js). The pictures and tables work offline.";
}
</script>
"""
