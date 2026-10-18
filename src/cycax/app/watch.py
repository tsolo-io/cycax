# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""`cycax watch` and `cycax view` (task cycax/31): build again on save, show the model live.

The watcher reloads the project code in the same process (build123d stays loaded, so a draft
build of a part takes about a second). The viewer is a small local web server: the page asks
for the model version every second and loads the new model when it changes.
"""

import contextlib
import http.server
import importlib.util
import json
import logging
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from cycax.app.project import Project


def forget_project_modules(project: Project):
    """Remove the project's modules from sys.modules, so the next load reads the new code."""
    root = str(project.root)
    for name, module in list(sys.modules.items()):
        file = getattr(module, "__file__", None) or ""
        if file.startswith(root) and "site-packages" not in file:
            del sys.modules[name]
            # The .pyc check uses mtime (1 s) + size: a quick save of the same size would load
            # the old code. Remove the cached bytecode.
            with contextlib.suppress(OSError, ValueError, NotImplementedError):
                Path(importlib.util.cache_from_source(file)).unlink(missing_ok=True)
    project._targets = None  # noqa: SLF001 - the project's own cache


def affected_targets(project: Project, changed: set[Path], wanted: list[str] | None) -> list[str]:
    """The targets to build after `changed` files were saved: the targets in those files; all
    (wanted) targets when a changed file has no targets (a helper module)."""
    refs = project.targets()
    names = wanted or list(refs)
    in_changed = [name for name in names if name in refs and refs[name].file in changed]
    files_with_targets = {ref.file for ref in refs.values()}
    if any(path not in files_with_targets for path in changed):
        return names
    return in_changed


def watch(
    project: Project,
    *,
    on_change: Callable[[list[str]], None],
    wanted: list[str] | None = None,
    stop: threading.Event | None = None,
):
    """Call `on_change(targets)` each time Python files of the project are saved."""
    import watchfiles  # noqa: PLC0415

    folders = sorted({p for p in (project.root / s for s in project.settings.sources) if p.exists()})
    for changes in watchfiles.watch(*folders, stop_event=stop, debounce=300, step=100):
        changed = {Path(path).resolve() for _, path in changes if path.endswith(".py")}
        if not changed:
            continue
        forget_project_modules(project)
        try:
            targets = affected_targets(project, changed, wanted)
        except Exception:  # noqa: BLE001 - a syntax error while typing must not stop the watch
            logging.exception("Cannot load the project")
            continue
        if targets:
            on_change(targets)


@dataclass
class LiveModel:
    """The model the viewer shows; `version` changes each time `update()` gets a new file."""

    path: Path | None = None
    version: int = 0
    error: str = ""
    lock: threading.Lock = field(default_factory=threading.Lock)

    def update(self, path: Path | None, error: str = ""):
        with self.lock:
            if path is not None:
                self.path = path
            self.error = error
            self.version += 1


def serve(model: LiveModel, title: str, port: int = 0) -> http.server.ThreadingHTTPServer:
    """Start the viewer on localhost (a free port when 0). Returns the running server."""

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_args):  # quiet
            pass

        def _send(self, body: bytes, content_type: str, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802 - http.server API
            if self.path == "/":
                self._send(VIEWER_PAGE.replace("{title}", title).encode(), "text/html; charset=utf-8")
            elif self.path == "/version":
                with model.lock:
                    data = {
                        "version": model.version,
                        "error": model.error,
                        "kind": model.path.suffix.lstrip(".") if model.path else "",
                    }
                self._send(json.dumps(data).encode(), "application/json")
            elif self.path.startswith("/model") and model.path and model.path.exists():
                self._send(model.path.read_bytes(), "application/octet-stream")
            else:
                self._send(b"not found", "text/plain", 404)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, name="cycax-viewer", daemon=True).start()
    return server


def wait_forever(stop: threading.Event | None = None):
    while not (stop and stop.is_set()):
        time.sleep(0.5)


VIEWER_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - CyCAx view</title>
<style>
html, body { margin: 0; height: 100%; background: #eaeaea; font-family: system-ui, sans-serif; }
#status { position: fixed; top: 0.6rem; left: 0.8rem; background: rgba(255,255,255,0.9); padding: 0.2rem 0.6rem;
  border-radius: 4px; font-size: 0.9rem; color: #222; }
#status.error { background: #ffe5e5; color: #900; white-space: pre-wrap; max-width: 80vw; }
</style></head>
<body><div id="status">Loading {title} ...</div>
<script type="importmap">
{"imports": {"three": "https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js",
             "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
const status = document.getElementById("status");
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xeaeaea);
scene.add(new THREE.HemisphereLight(0xffffff, 0x666666, 2.4));
const light = new THREE.DirectionalLight(0xffffff, 1.3);
light.position.set(1, 2, 3);
scene.add(light);
const camera = new THREE.PerspectiveCamera(45, innerWidth / innerHeight, 0.1, 1e6);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(devicePixelRatio);
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
let current = null, version = -1, fitted = false;
function show(object, label) {
  if (current) scene.remove(current);
  current = object;
  scene.add(object);
  if (!fitted) {  // keep the user's camera on later updates
    const box = new THREE.Box3().setFromObject(object);
    const size = box.getSize(new THREE.Vector3()).length() || 1;
    const centre = box.getCenter(new THREE.Vector3());
    camera.position.copy(centre).add(new THREE.Vector3(size, size * 0.7, size));
    camera.near = size / 1000; camera.far = size * 100; camera.updateProjectionMatrix();
    controls.target.copy(centre); controls.update();
    fitted = true;
  }
  status.className = ""; status.textContent = label;
}
function load(kind, v) {
  const url = "/model?v=" + v;
  const label = "{title} - version " + v + " - " + new Date().toLocaleTimeString();
  if (kind === "glb") new GLTFLoader().load(url, (g) => show(g.scene, label));
  else new STLLoader().load(url, (geometry) => {
    geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0x6f93c9, roughness: 0.6 }));
    mesh.rotation.x = -Math.PI / 2;
    show(mesh, label);
  });
}
async function poll() {
  try {
    const data = await (await fetch("/version")).json();
    if (data.error) { status.className = "error"; status.textContent = data.error; }
    if (data.version !== version) { version = data.version; if (data.kind && !data.error) load(data.kind, version); }
  } catch (e) { status.className = "error"; status.textContent = "cycax view stopped."; }
  setTimeout(poll, 1000);
}
poll();
addEventListener("resize", () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight); });
(function animate() { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); })();
</script></body></html>
"""
