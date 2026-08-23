"""The file carrier a ``format: file`` scalar declares.

``File`` is shared rather than per-package because it is a *nominal* pydantic
model and pydantic validates a ``BaseModel``-typed field by ``isinstance``. With
one copy of the class per generated distribution, a model in package A rejects a
``File`` built by package B outright with a ``ValidationError`` — there is no
``from_attributes`` fallback on a plain model field. The class reaches a model
field, a block ``Input`` field and an HTTP server input carrier, so all three
have to agree on one class object.
"""

from __future__ import annotations

import base64
from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
)

__all__ = ["File"]


# The carrier is a pydantic model rather than a plain dataclass because it has
# to survive the wire: every target writes `{name, mimeType, data}` with the
# bytes as base64, and only a model can carry the alias and the byte codec that
# make Python write — and read — the same three members. The field keeps its
# Python name so `File(name=..., mime_type=..., data=...)` type-checks: a bare
# `alias` makes mypy synthesise `__init__` from the wire name instead, while
# the alias pair carries `mimeType` in both directions on the wire.
class File(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    mime_type: str = Field(
        validation_alias=AliasChoices("mimeType", "mime_type"),
        serialization_alias="mimeType",
    )
    data: bytes

    @field_validator("data", mode="before")
    @classmethod
    def _decode_data(cls, value: Any) -> Any:
        if isinstance(value, str):
            return base64.b64decode(value)
        return value

    @field_serializer("data")
    def _encode_data(self, value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")
