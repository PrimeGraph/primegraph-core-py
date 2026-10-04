"""``whole_int`` / ``whole_int_text`` — OpenAPI ``integer`` is defined by value."""

from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import BaseModel, BeforeValidator, StrictInt, ValidationError

from primegraph_core import runtime, whole_int, whole_int_text

WholeInt = Annotated[StrictInt, BeforeValidator(runtime.whole_int)]
WholeIntText = Annotated[StrictInt, BeforeValidator(runtime.whole_int_text)]


class Counted(BaseModel):
    n: WholeInt


class Param(BaseModel):
    n: WholeIntText


@pytest.mark.parametrize(
    ("document", "expected"),
    [
        ('{"n": 1}', 1),
        ('{"n": 1.0}', 1),
        ('{"n": 1e2}', 100),
        ('{"n": -2.50e1}', -25),
        ('{"n": 9007199254740993}', 9007199254740993),
    ],
)
def test_a_whole_json_number_reads_as_the_int_it_equals(document: str, expected: int) -> None:
    value = Counted.model_validate_json(document).n

    assert value == expected
    assert type(value) is int


@pytest.mark.parametrize("document", ['{"n": 1.5}', '{"n": true}', '{"n": "1"}', '{"n": null}'])
def test_anything_but_a_whole_number_is_still_refused(document: str) -> None:
    with pytest.raises(ValidationError):
        Counted.model_validate_json(document)


def test_python_values_follow_the_same_rule() -> None:
    assert Counted(n=3.0).n == 3  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Counted(n=True)
    with pytest.raises(ValidationError):
        Counted(n=3.25)  # type: ignore[arg-type]


def test_whole_int_leaves_non_floats_and_fractions_as_they_are() -> None:
    marker = object()

    assert whole_int(marker) is marker
    assert whole_int(True) is True
    assert whole_int("2.0") == "2.0"
    assert whole_int(2.5) == 2.5
    assert whole_int(float("inf")) == float("inf")
    assert type(whole_int(2.0)) is int


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("7", 7),
        ("+7", 7),
        ("-7", -7),
        ("1.0", 1),
        ("1e2", 100),
        ("1E+2", 100),
        ("100.00e-2", 1),
        ("9223372036854775807", 9223372036854775807),
        ("9223372036854775808", 9223372036854775808),
        ("-9223372036854775808", -9223372036854775808),
        ("9007199254740993.0", 9007199254740993),
    ],
)
def test_integer_text_reads_as_the_int_it_spells(text: str, expected: int) -> None:
    value = whole_int_text(text)

    assert value == expected
    assert type(value) is int
    assert Param(n=text).n == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "text",
    ["1.5", "1e-1", "abc", "", " 1", "1 ", "1\n", "0x10", "1_000", "9223372036854775809", "1e999999999"],
)
def test_text_that_is_not_a_whole_number_in_range_stays_text(text: str) -> None:
    assert whole_int_text(text) is text
    with pytest.raises(ValidationError):
        Param(n=text)  # type: ignore[arg-type]


def test_whole_int_text_leaves_non_text_as_it_is() -> None:
    assert whole_int_text(5) == 5
    assert whole_int_text(5.0) == 5.0
    assert type(whole_int_text(5.0)) is float
    assert whole_int_text(None) is None
