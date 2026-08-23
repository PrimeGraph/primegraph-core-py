"""``File`` — construction, the wire codec, and the cross-package failure mode."""

from __future__ import annotations

import base64

import pytest
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, ValidationError

from primegraph_core import File

PNG = b"\x89PNG\r\n\x1a\n"
PNG_B64 = base64.b64encode(PNG).decode("ascii")


def test_constructs_from_python_names() -> None:
    f = File(name="a.png", mime_type="image/png", data=PNG)

    assert f.name == "a.png"
    assert f.mime_type == "image/png"
    assert f.data == PNG


def test_validates_from_the_wire_shape() -> None:
    f = File.model_validate({"name": "a.png", "mimeType": "image/png", "data": PNG_B64})

    assert f.mime_type == "image/png"
    # The base64 text a producer wrote arrives decoded, not as text.
    assert f.data == PNG


def test_validates_from_the_python_alias_too() -> None:
    f = File.model_validate({"name": "a.png", "mime_type": "image/png", "data": PNG})

    assert f.mime_type == "image/png"


def test_serializes_to_the_wire_shape() -> None:
    f = File(name="a.png", mime_type="image/png", data=PNG)

    assert f.model_dump(mode="json", by_alias=True) == {
        "name": "a.png",
        "mimeType": "image/png",
        "data": PNG_B64,
    }


def test_round_trips_through_the_wire() -> None:
    f = File(name="a.png", mime_type="image/png", data=PNG)

    assert File.model_validate(f.model_dump(mode="json", by_alias=True)) == f


def test_rejects_a_missing_member() -> None:
    with pytest.raises(ValidationError) as caught:
        File.model_validate({"name": "a.png", "data": PNG_B64})

    assert caught.value.errors()[0]["type"] == "missing"


def test_rejects_a_wrong_type() -> None:
    with pytest.raises(ValidationError):
        File.model_validate({"name": 7, "mimeType": "image/png", "data": PNG_B64})


class Attachment(BaseModel):
    """A generated model that declares a ``format: file`` member."""

    title: str
    payload: File


class ForeignFile(BaseModel):
    """A byte-identical second copy of ``File``, as a second generated package
    would have carried it before this distribution existed."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    mime_type: str = Field(
        validation_alias=AliasChoices("mimeType", "mime_type"),
        serialization_alias="mimeType",
    )
    data: bytes


def test_a_model_field_accepts_an_instance_of_this_class() -> None:
    f = File(name="a.png", mime_type="image/png", data=PNG)

    a = Attachment(title="logo", payload=f)

    assert a.payload is f


def test_a_model_field_rejects_a_foreign_copy_of_the_class() -> None:
    # The reason this class is shared: pydantic validates a BaseModel-typed
    # field by isinstance and offers no from_attributes fallback, so a second
    # copy of File is not merely a different name — it is rejected outright.
    foreign = ForeignFile(name="a.png", mime_type="image/png", data=PNG)

    with pytest.raises(ValidationError) as caught:
        Attachment(title="logo", payload=foreign)  # type: ignore[arg-type]

    assert caught.value.errors()[0]["type"] == "model_type"


def test_a_model_field_round_trips_the_wire_shape() -> None:
    a = Attachment.model_validate(
        {"title": "logo", "payload": {"name": "a.png", "mimeType": "image/png", "data": PNG_B64}}
    )

    assert a.payload.data == PNG
    assert a.model_dump(mode="json", by_alias=True)["payload"]["mimeType"] == "image/png"
