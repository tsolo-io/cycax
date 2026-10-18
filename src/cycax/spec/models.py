# SPDX-FileCopyrightText: 2026 Tsolo.io
#
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for spec version 2.

Feature objects keep `extra="allow"`: each feature type has its own fields (holes, bends,
flange cuts, ...). The models check the shared structure; engines check type-specific fields.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

SPEC_VERSION = 2

Colour = Annotated[list[float], Field(min_length=3, max_length=4)]


class SpecVersionError(ValueError):
    """The spec is not version 2 (for example an old V1 file)."""


class _Open(BaseModel):
    model_config = ConfigDict(extra="allow")


class RotateEntry(BaseModel):
    axis: Literal["x", "y", "z"]
    angle: float  # degrees


class Material(_Open):
    name: str
    code: str | None = None
    standard: str | None = None
    density: float | None = None  # g/cm³ (cycax.materials)


class PartMeta(_Open):
    """Not part of the hash."""

    description: str | None = None
    notes: str | None = None
    doc_view: str | None = None
    material: Material | None = None
    colour: Colour | None = None
    manufacture: dict | None = None


class Feature(_Open):
    type: str
    action: str
    name: str | None = None
    side: str | None = None


class PartSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_version: Literal[2]
    kind: Literal["part"]
    name: str = Field(min_length=1)
    features: list[Feature] = Field(min_length=1)  # features[0] is the base shape
    subtract: list[Feature] = Field(default_factory=list)
    meta: PartMeta = Field(default_factory=PartMeta)


class PartEntryMeta(_Open):
    """Not part of the hash."""

    colour: Colour | None = None


class PartEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)  # the part number
    instance: str = Field(min_length=1)  # the name of this instance in the assembly
    hash: str = Field(min_length=1)  # the part's spec hash (cache key)
    x: float
    y: float
    z: float
    x_size: float
    y_size: float
    z_size: float
    center: bool = False
    rotate: list[RotateEntry] = Field(default_factory=list)
    # The placement (task cycax/32): 4 x 4 row-major, part coordinates -> world, mm. When it is
    # there, engines use it and ignore x/y/z/rotate (kept for readers).
    transform: list[list[float]] | None = None
    meta: PartEntryMeta = Field(default_factory=PartEntryMeta)


class AssemblyMeta(_Open):
    """Not part of the hash."""

    description: str | None = None
    notes: str | None = None


class AssemblySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spec_version: Literal[2]
    kind: Literal["assembly"]
    name: str = Field(min_length=1)
    parts: list[PartEntry]
    # Mates in the order solved (task cycax/38): type, moving/target {instance, anchor}, options.
    mates: list[dict] | None = None
    meta: AssemblyMeta = Field(default_factory=AssemblyMeta)


def validate_spec(data: dict) -> PartSpec | AssemblySpec:
    """Validate a part or assembly spec.

    Raises:
        SpecVersionError: The spec is not version 2.
        pydantic.ValidationError: The spec does not match the models.
    """
    version = data.get("spec_version")
    if version != SPEC_VERSION:
        msg = (
            f"Spec version {version!r} is not supported, expected {SPEC_VERSION}. "
            "Compile the source again with the current cycax."
        )
        raise SpecVersionError(msg)
    if data.get("kind") == "assembly":
        return AssemblySpec.model_validate(data)
    if data.get("kind") == "part":
        return PartSpec.model_validate(data)
    msg = f"Unknown spec kind {data.get('kind')!r}, expected 'part' or 'assembly'."
    raise SpecVersionError(msg)


def json_schemas() -> dict[str, dict]:
    """The JSON Schemas for workers that do not use these models."""
    return {
        "part.schema.json": PartSpec.model_json_schema(),
        "assembly.schema.json": AssemblySpec.model_json_schema(),
    }


__all__ = [
    "SPEC_VERSION",
    "AssemblySpec",
    "PartSpec",
    "SpecVersionError",
    "ValidationError",
    "json_schemas",
    "validate_spec",
]
