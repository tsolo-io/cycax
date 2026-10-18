# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""`cycax watch` and `cycax view` (task cycax/31)."""

import json
import threading
import time
import urllib.request

from cycax.app.project import Project, Settings
from cycax.app.watch import LiveModel, affected_targets, forget_project_modules, serve, watch

PART = """from cycax import cycax_part
from cycax.cycad import Print3D


@cycax_part
def {name}() -> Print3D:
    return Print3D(part_no="{name}", x_size={size}, y_size=10, z_size=2)
"""


def make_project(tmp_path) -> Project:
    (tmp_path / "parts").mkdir()
    (tmp_path / "parts" / "a.py").write_text(PART.format(name="a", size=10))
    (tmp_path / "parts" / "b.py").write_text(PART.format(name="b", size=10))
    (tmp_path / "parts" / "helper.py").write_text("WIDTH = 3\n")
    settings = Settings()
    settings.sources = ["parts"]
    return Project(tmp_path, settings)


def test_affected_targets(tmp_path):
    project = make_project(tmp_path)
    parts = (tmp_path / "parts").resolve()
    assert affected_targets(project, {parts / "a.py"}, None) == ["a"]
    assert sorted(affected_targets(project, {parts / "helper.py"}, None)) == ["a", "b"]
    assert affected_targets(project, {parts / "helper.py"}, ["b"]) == ["b"]


def test_reload_reads_the_new_code(tmp_path):
    project = make_project(tmp_path)
    assert project.targets()["a"].target.make()[0].x_size == 10
    (tmp_path / "parts" / "a.py").write_text(PART.format(name="a", size=25))
    forget_project_modules(project)
    assert project.targets()["a"].target.make()[0].x_size == 25


def test_watch_calls_back_on_save(tmp_path):
    project = make_project(tmp_path)
    project.targets()
    seen, stop = [], threading.Event()

    def on_change(targets):
        seen.append(targets)
        stop.set()

    thread = threading.Thread(target=watch, args=(project,), kwargs={"on_change": on_change, "stop": stop}, daemon=True)
    thread.start()
    time.sleep(0.5)
    (tmp_path / "parts" / "b.py").write_text(PART.format(name="b", size=30))
    thread.join(timeout=10)
    assert seen == [["b"]]


def test_viewer_serves_the_live_model(tmp_path):
    model = LiveModel()
    server = serve(model, "plate")
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        assert b"three" in urllib.request.urlopen(base + "/").read()  # noqa: S310 - local test server
        first = json.loads(urllib.request.urlopen(base + "/version").read())  # noqa: S310
        glb = tmp_path / "plate.glb"
        glb.write_bytes(b"glTF-data")
        model.update(glb)
        second = json.loads(urllib.request.urlopen(base + "/version").read())  # noqa: S310
        assert second["version"] == first["version"] + 1
        assert second["kind"] == "glb"
        assert urllib.request.urlopen(base + "/model?v=1").read() == b"glTF-data"  # noqa: S310
    finally:
        server.shutdown()
