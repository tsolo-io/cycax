# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""How the CLI shows things (task cycax/18): one line per target, a summary, errors with a fix.

Colour is never the only signal: every line has a symbol and a word. `--plain` (and NO_COLOR,
or a terminal without Unicode) gives plain text with no colour, symbols or spinner.
"""

import json
import os
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.text import Text

from cycax.app.errors import CycaxError
from cycax.app.events import Event, TargetDone, TargetFailed, TargetProgress, TargetStarted


class Output:
    def __init__(self, *, plain: bool = False, json_mode: bool = False):
        unicode_ok = (sys.stdout.encoding or "").lower().startswith("utf")
        self.plain = plain or bool(os.environ.get("NO_COLOR")) or not unicode_ok
        self.json_mode = json_mode
        self.console = Console(no_color=self.plain, highlight=False, emoji=False)
        self.err = Console(stderr=True, no_color=self.plain, highlight=False, emoji=False)

    # -- symbols --------------------------------------------------------------------------
    def sym(self, kind: str) -> str:
        plain = {"ok": "ok", "fail": "FAILED", "cache": "cached", "busy": "...", "wait": "-", "warn": "!"}
        fancy = {"ok": "✓", "fail": "✗", "cache": "↻", "busy": "•", "wait": "·", "warn": "!"}
        return (plain if self.plain else fancy)[kind]

    def print(self, *args, **kwargs):
        kwargs.setdefault("soft_wrap", True)  # long paths stay on one line
        self.console.print(*args, **kwargs)

    def print_json(self, data):
        self.console.print_json(json.dumps(data, default=str))

    def error(self, error: CycaxError):
        style = "" if self.plain else "bold red"
        self.err.print(Text(f"{self.sym('fail')} {error.message}", style=style), soft_wrap=True)
        if error.fix:
            self.err.print(f"  To fix: {error.fix}", soft_wrap=True)

    def table(self, rows: list[dict], columns: list[str]):
        if self.json_mode:
            self.print_json(rows)
            return
        widths = [max([len(c.replace("_", " ")), *(len(str(row.get(c, ""))) for row in rows)]) for c in columns]
        fixed = sum(widths[:-1]) + 2 * (len(columns) - 1)
        # Names and paths stay whole; only the last column (e.g. a description) is cut. A
        # narrow terminal (or a pipe, 80 columns) gets longer lines, not fewer columns.
        last_width = max(self.console.width - fixed, 12)
        table = Table(box=None, pad_edge=False)
        for index, column in enumerate(columns):
            last = index == len(columns) - 1
            table.add_column(
                column.replace("_", " ").title(),
                no_wrap=True,
                overflow="ellipsis",
                max_width=min(last_width, widths[index]) if last else None,
            )
        for row in rows:
            table.add_row(*[str(row.get(c, "")) for c in columns])
        self.console.print(table, width=max(self.console.width, fixed + min(last_width, widths[-1])))


class BuildView:
    """Shows build events: one line per target that changes in place, then a summary."""

    def __init__(self, out: Output, header: str):
        self.out = out
        self.header = header
        self.rows: dict[str, dict] = {}
        self.start = time.monotonic()
        self.live: Live | None = None

    def __enter__(self):
        if not self.out.plain and not self.out.json_mode and self.out.console.is_terminal:
            self.live = Live(self._render(), console=self.out.console, refresh_per_second=8, transient=False)
            self.live.__enter__()
        elif not self.out.json_mode:
            self.out.print(self.header)
        return self

    def __exit__(self, *exc):
        if self.live:
            self.live.update(self._render())
            self.live.__exit__(*exc)
        return False

    def _render(self):
        table = Table.grid(padding=(0, 2))
        table.add_row(Text(self.header, style="dim"))
        for name, row in self.rows.items():
            table.add_row(Text.assemble(f"  {row['symbol']} ", (name, "bold"), f"  {row['kind']:<9} ", row["text"]))
        return table

    def on_event(self, event: Event):
        row = self.rows.setdefault(event.target, {"symbol": self.out.sym("wait"), "kind": "", "text": ""})
        if isinstance(event, TargetStarted):
            row.update(symbol=self.out.sym("busy"), kind=event.kind, text="building")
        elif isinstance(event, TargetProgress):
            row.update(text=event.message)
        elif isinstance(event, TargetDone):
            symbol = self.out.sym("cache") if event.cached else self.out.sym("ok")
            word = "from cache" if event.cached else f"built in {event.seconds:.1f} s"
            row.update(symbol=symbol, kind=event.kind, text=f"{word}  ({' '.join(sorted(event.files))})")
        elif isinstance(event, TargetFailed):
            first = event.error.splitlines()[0] if event.error else ""
            row.update(symbol=self.out.sym("fail"), text=f"failed: {first[:100]}")
        if self.live:
            self.live.update(self._render())
        elif not self.out.json_mode and isinstance(event, TargetDone | TargetFailed):
            self.out.print(f"  {row['symbol']} {event.target}  {row['kind']}  {row['text']}")

    def summary(self, result, build_folder: Path):
        if self.out.json_mode:
            self.out.print_json(
                {
                    name: {
                        "kind": t.kind,
                        "files": {k: str(v) for k, v in t.files.items()},
                        "cached": t.cached,
                        "error": t.error,
                        "fix": t.fix,
                    }
                    for name, t in result.targets.items()
                }
            )
            return
        built = sum(1 for t in result.targets.values() if t.error is None and not t.cached)
        cached = sum(1 for t in result.targets.values() if t.error is None and t.cached)
        failed = [t for t in result.targets.values() if t.error]
        parts = [f"{built} built", f"{cached} from cache"] + ([f"{len(failed)} failed"] if failed else [])
        self.out.print(f"\n  {' · '.join(parts)}   in {time.monotonic() - self.start:.1f} s")
        self.out.print(f"  Results: {build_folder}")
        for target in failed:
            self.out.error(CycaxError(f"{target.name}: {target.error}", target.fix))
