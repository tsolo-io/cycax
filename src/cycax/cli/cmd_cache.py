# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""`cycax cache list | open | clean`: the local cache (`<cache folder>/<hash>/`)."""

import datetime
import json
import shutil
import time
from pathlib import Path
from typing import Annotated

import typer

from cycax.app.errors import UsageError

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, no_args_is_help=True)


def _state():
    from cycax.cli.main import state  # noqa: PLC0415 - main imports this module

    return state()


def cache_root() -> Path:
    return Path(_state().project.settings.cache_folder).expanduser()


def entries(root: Path) -> list[dict]:
    """One row per cache hash: name, files, size and the last time it was used."""
    rows = []
    if not root.is_dir():
        return rows
    for folder in root.iterdir():
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        files = [p for p in folder.iterdir() if p.is_file()]
        name = ""
        spec = folder / "spec.json"
        if spec.is_file():
            try:
                name = json.loads(spec.read_text()).get("name", "")
            except (OSError, ValueError):
                name = ""
        used = max((p.stat().st_mtime for p in files), default=folder.stat().st_mtime)
        rows.append(
            {
                "hash": folder.name,
                "name": name,
                "files": len([p for p in files if p.name not in ("spec.json", "manifest.json")]),
                "size": sum(p.stat().st_size for p in files),
                "used": used,
            }
        )
    return rows


def _size(size: float) -> str:
    for unit in ("B", "kB", "MB", "GB"):
        if size < 1000:  # noqa: PLR2004
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1000
    return f"{size:.1f} TB"


def _when(timestamp: float) -> str:
    return datetime.datetime.fromtimestamp(timestamp).astimezone().strftime("%Y-%m-%d %H:%M")


def _find(root: Path, cache_hash: str) -> Path:
    matches = [row["hash"] for row in entries(root) if row["hash"].startswith(cache_hash)]
    if len(matches) != 1:
        msg = f"No cache entry {cache_hash!r}." if not matches else f"{cache_hash!r} matches more than one entry."
        raise UsageError(msg, fix="To see the entries: cycax cache list")
    return root / matches[0]


@app.command("list")
def cache_list(
    *,
    sort: Annotated[str, typer.Option(help="size, used or name")] = "used",
):
    """Show the cache entries, newest first."""
    from cycax.cli.main import guarded  # noqa: PLC0415

    @guarded
    def run():
        st = _state()
        root = cache_root()
        rows = entries(root)
        key = {"size": lambda r: r["size"], "used": lambda r: r["used"], "name": lambda r: r["name"]}.get(sort)
        if key is None:
            msg = f"Unknown sort {sort!r}."
            raise UsageError(msg, fix="Use size, used or name.")
        rows.sort(key=key, reverse=sort != "name")
        if st.out.json_mode:
            st.out.print_json(rows)
            return
        shown = [{**r, "size": _size(r["size"]), "used": _when(r["used"])} for r in rows]
        st.out.table(shown, ["hash", "name", "files", "size", "used"])
        st.out.print(f"\n{len(rows)} entries, {_size(sum(r['size'] for r in rows))} in {root}")

    run()


@app.command("open")
def cache_open(cache_hash: Annotated[str, typer.Argument(help="The hash (or its start) of the entry.")]):
    """Open a cache entry folder in the file manager."""
    from cycax.app.results import open_path  # noqa: PLC0415
    from cycax.cli.main import guarded  # noqa: PLC0415

    @guarded
    def run():
        open_path(_find(cache_root(), cache_hash))

    run()


@app.command("clean")
def cache_clean(
    hashes: Annotated[list[str] | None, typer.Argument(help="Entries to remove (hash or its start).")] = None,
    *,
    all_entries: Annotated[bool, typer.Option("--all", help="Remove all entries.")] = False,
    older_than: Annotated[int | None, typer.Option(help="Remove entries not used for this many days.")] = None,
):
    """Remove cache entries. The next build makes them again. Asks first, unless --yes."""
    from cycax.cli.main import guarded  # noqa: PLC0415

    @guarded
    def run():
        st = _state()
        root = cache_root()
        if all_entries:
            folders = [root / r["hash"] for r in entries(root)]
        elif older_than is not None:
            limit = time.time() - older_than * 86400
            folders = [root / r["hash"] for r in entries(root) if r["used"] < limit]
        elif hashes:
            folders = [_find(root, h) for h in hashes]
        else:
            msg = "Tell which entries to remove."
            raise UsageError(msg, fix="cycax cache clean <hash>, --older-than <days> or --all")
        if not folders:
            st.out.print("Nothing to remove.")
            return
        if not st.yes:
            if not st.can_ask:
                msg = f"This removes {len(folders)} cache entries."
                raise UsageError(msg, fix="Add --yes to remove them without a question.")
            if not typer.confirm(f"Remove {len(folders)} cache entries from {root}?", default=False):
                raise typer.Exit(0)
        for folder in folders:
            shutil.rmtree(folder)
        if st.out.json_mode:
            st.out.print_json({"removed": [f.name for f in folders]})
        else:
            st.out.print(f"{st.out.sym('ok')} Removed {len(folders)} cache entries.")

    run()
