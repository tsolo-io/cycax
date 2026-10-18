# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Quality profiles, artifact names and best-file selection.

Profiles change WHAT an engine does (mesh deviation, OpenSCAD `$fn`, image size), not WHICH
engine runs. Artifacts in the cache are named `<name>-<engine>-<profile>.<ext>`. When several
engines made the same format, the score table decides which file is "best": highest score
wins, ties go to the engine order FreeCAD, build123d, OpenSCAD.

The live table is the NATS KV bucket `cycax_quality` (edited in the cycax-server UI, seeded by
the CLI from `DEFAULT_SCORES`); without NATS, `DEFAULT_SCORES` applies, and a project's
`cycax.toml` `[quality]` table can override single entries. See cycax-server
docs/content/nats-protocol.md §5 and §6.
"""

import re
from dataclasses import dataclass

PROFILES = ("draft", "standard", "fine")
DEFAULT_PROFILE = "standard"

# What each profile means per engine/format. First proposal (2026-10-17); tune after tests.
PROFILE_SETTINGS = {
    "stl_linear_deflection_mm": {"draft": 0.5, "standard": 0.01, "fine": 0.001},
    "stl_angular_deflection_rad": {"draft": 0.5, "standard": 0.1, "fine": 0.05},
    "openscad_fn": {"draft": 16, "standard": 64, "fine": 256},
    "png_size_px": {"draft": 800, "standard": 1600, "fine": 3200},
}

# Tie-break order (first wins) when scores are equal.
ENGINE_ORDER = ("freecad", "build123d", "python", "openscad", "blender")

_PROFILE_BASE = {"draft": 10, "standard": 50, "fine": 90}
# OpenSCAD meshes are coarse even at high `$fn` (martin: its slow render is not as good as
# FreeCAD's default), so it scores lower than FreeCAD/build123d at the same profile.
_ENGINE_OFFSET = {"freecad": 3, "build123d": 2, "python": 2, "openscad": -40, "blender": 0}
# Blender renders are the best images.
_FORMAT_ENGINE_BONUS = {("png", "blender"): 8}
_FORMATS = (
    "stl",
    "step",
    "glb",
    "fcstd",
    "dxf",
    "svg",
    "png",
    "scad",
    "blend",
    "3mf",
    "json",
    "views.png",
    "drawing.svg",
)
# Formats whose file extension is not the format name.
FORMAT_EXT = {"summary": "json", "views": "views.png", "drawing": "drawing.svg"}


def file_ext(fmt: str) -> str:
    """The file extension of a format: "summary" -> "json", others the same."""
    return FORMAT_EXT.get(fmt.lower(), fmt.lower())


def _default_scores() -> dict[str, int]:
    scores = {}
    for engine, offset in _ENGINE_OFFSET.items():
        for fmt in _FORMATS:
            for profile, base in _PROFILE_BASE.items():
                scores[f"{engine}.{fmt}.{profile}"] = base + offset + _FORMAT_ENGINE_BONUS.get((fmt, engine), 0)
    return scores


DEFAULT_SCORES: dict[str, int] = _default_scores()

_ARTIFACT = re.compile(
    r"^(?P<name>[^-/]+)-(?P<engine>[a-z0-9_]+)(?:-(?P<profile>draft|standard|fine))?\.(?P<ext>\w+(?:\.\w+)?)$"
)


@dataclass(frozen=True)
class Artifact:
    filename: str
    name: str
    engine: str
    profile: str
    ext: str  # lower case

    def key(self) -> str:
        return f"{self.engine}.{self.ext}.{self.profile}"


def artifact_name(name: str, engine: str, profile: str, ext: str) -> str:
    """The cache file name of an artifact: `<name>-<engine>-<profile>.<ext>`."""
    if profile not in PROFILES:
        msg = f"Unknown profile {profile!r}, expected one of {PROFILES}."
        raise ValueError(msg)
    return f"{name}-{engine}-{profile}.{file_ext(ext)}"


def parse_artifact_name(filename: str) -> Artifact | None:
    """Parse `<name>-<engine>-<profile>.<ext>`; old `<name>-<engine>.<ext>` names count as
    profile `standard`. Returns None for other files (spec.json, logs, imports)."""
    match = _ARTIFACT.match(filename)
    if not match or filename.endswith(".log") or match["engine"] == "import":
        return None
    return Artifact(
        filename=filename,
        name=match["name"],
        engine=match["engine"],
        profile=match["profile"] or DEFAULT_PROFILE,
        ext=match["ext"].lower(),
    )


def score(artifact: Artifact, table: dict[str, int] | None = None) -> int:
    scores = DEFAULT_SCORES if table is None else {**DEFAULT_SCORES, **table}
    return scores.get(artifact.key(), _PROFILE_BASE.get(artifact.profile, 0))


def satisfies(artifact: Artifact, requested_profile: str) -> bool:
    """An artifact at or above the requested profile satisfies the request."""
    return PROFILES.index(artifact.profile) >= PROFILES.index(requested_profile)


def select_best(
    filenames: list[str], ext: str, *, table: dict[str, int] | None = None, min_profile: str = "draft"
) -> str | None:
    """Pick the best cached file of one format (e.g. "stl") from a list of file names.

    Args:
        filenames: File names under one hash (no `<hash>/` prefix).
        ext: The format, e.g. "stl".
        table: Score overrides (from KV or cycax.toml); merged over DEFAULT_SCORES.
        min_profile: Only files at or above this profile are candidates.
    """
    candidates = []
    for filename in filenames:
        artifact = parse_artifact_name(filename)
        if artifact and artifact.ext == file_ext(ext) and satisfies(artifact, min_profile):
            # The flat pattern of a sheet-metal part (`<name>_unfold`) is only the answer for DXF;
            # its STEP is not the part (found by the cross-engine tests: a "best STEP" was flat).
            if artifact.name.endswith("_unfold") and ext.lower() != "dxf":
                continue
            candidates.append(artifact)
    if not candidates:
        return None

    def rank(artifact: Artifact):
        order = ENGINE_ORDER.index(artifact.engine) if artifact.engine in ENGINE_ORDER else len(ENGINE_ORDER)
        return (-score(artifact, table), order)

    return min(candidates, key=rank).filename
