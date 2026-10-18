# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Build events. The builder sends them; the CLI, the terminal UI and `cycax.build()` show or
collect them."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Event:
    target: str


@dataclass
class TargetStarted(Event):
    kind: str = "part"


@dataclass
class TargetProgress(Event):
    message: str = ""


@dataclass
class TargetDone(Event):
    kind: str = "part"
    files: dict[str, Path] = field(default_factory=dict)  # format -> file in the build folder
    cached: bool = False  # True when nothing had to be built
    seconds: float = 0.0


@dataclass
class TargetFailed(Event):
    error: str = ""
    fix: str | None = None
