"""The DSL error vocabulary: identity, coercion, matching and the view."""

from __future__ import annotations

import logging

import pytest
from pydantic import BaseModel

from primegraph_core import (
    DSL_ERROR_MESSAGES,
    DslError,
    DslErrorView,
    coerce_error,
    default_error_message,
    error_matches,
    error_view,
    transport_error_code,
)


class OutOfStock(BaseModel):
    sku: str
    remaining: int


class StandardError(BaseModel):
    code: str
    message: str


def test_dsl_error_is_an_exception_carrying_a_code_and_a_typed_payload() -> None:
    payload = OutOfStock(sku="A-1", remaining=0)

    err = DslError("out-of-stock", payload)

    assert isinstance(err, Exception)
    assert err.code == "out-of-stock"
    assert err.payload is payload


def test_dsl_error_survives_raise_and_catch() -> None:
    with pytest.raises(DslError) as caught:
        raise DslError("not-found", {"id": "7"})

    assert caught.value.code == "not-found"
    assert caught.value.payload == {"id": "7"}


def test_dsl_error_str_is_the_code() -> None:
    assert str(DslError("aborted", None)) == "aborted"


def test_dsl_error_view_carries_code_and_payload() -> None:
    view = DslErrorView("not-found", {"id": "7"})

    assert view.code == "not-found"
    assert view.payload == {"id": "7"}
    assert view.to_json() == {"code": "not-found", "payload": {"id": "7"}}


def test_dsl_error_view_generic_parameterisation() -> None:
    # The emitted code annotates a catch binding as DslErrorView[Payload] and
    # the scope default constructs the bare class; both have to work.
    parameterised = DslErrorView[OutOfStock]
    view: DslErrorView[OutOfStock] = DslErrorView("out-of-stock", OutOfStock(sku="A-1", remaining=0))

    assert parameterised.__origin__ is DslErrorView  # type: ignore[attr-defined]
    assert view.payload.sku == "A-1"


def test_dsl_error_generic_parameterisation() -> None:
    assert DslError[OutOfStock].__origin__ is DslError  # type: ignore[attr-defined]


def test_default_error_message_knows_the_declared_codes() -> None:
    assert default_error_message("VALIDATION_FAILED") == "Request validation failed"
    assert default_error_message("already-exists") == "Resource already exists"
    assert DSL_ERROR_MESSAGES["NOT_FOUND"] == "Resource not found"


def test_default_error_message_falls_back_for_an_unknown_code() -> None:
    assert default_error_message("nothing-names-this") == "Internal server error"


def test_coerce_error_recognises_a_dsl_error_and_keeps_its_payload() -> None:
    payload = OutOfStock(sku="A-1", remaining=0)

    view = coerce_error(DslError("out-of-stock", payload), OutOfStock(sku="", remaining=0))

    assert view.code == "out-of-stock"
    assert view.payload is payload


def test_coerce_error_passes_a_plain_exception_through_as_internal_error() -> None:
    fallback = OutOfStock(sku="", remaining=0)

    view = coerce_error(RuntimeError("the database is on fire"), fallback)

    assert view.code == "INTERNAL_ERROR"
    assert view.payload is fallback


def test_coerce_error_fills_an_empty_text_payload_with_the_code_message() -> None:
    view = coerce_error(RuntimeError("boom"), "")

    assert view.code == "INTERNAL_ERROR"
    assert view.payload == "Internal server error"


def test_coerce_error_keeps_a_non_empty_text_payload() -> None:
    assert coerce_error(RuntimeError("boom"), "declared default").payload == "declared default"


def test_coerce_error_logs_a_foreign_failure(caplog: pytest.LogCaptureFixture) -> None:
    # The foreign error's own wording never reaches the caller, so it has to
    # reach the log instead.
    with caplog.at_level(logging.ERROR):
        coerce_error(RuntimeError("the database is on fire"), None)

    assert "the database is on fire" in caplog.text
    assert "INTERNAL_ERROR" in caplog.text


def test_coerce_error_does_not_log_a_dsl_error(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        coerce_error(DslError("not-found", None), None)

    assert caplog.text == ""


def test_transport_error_code_names_nothing_for_a_plain_exception() -> None:
    assert transport_error_code(RuntimeError("boom")) is None


def test_error_matches_accepts_a_payload_that_satisfies_the_declared_type() -> None:
    err = DslError("out-of-stock", OutOfStock(sku="A-1", remaining=0))

    assert error_matches(err, OutOfStock) is True


def test_error_matches_refuses_a_payload_the_declared_type_rejects() -> None:
    err = DslError("out-of-stock", OutOfStock(sku="A-1", remaining=0))

    assert error_matches(err, StandardError) is False


def test_error_matches_accepts_a_foreign_failure_against_the_standard_shape() -> None:
    # A catch declaring {code, message} handles any failure, DSL or SDK.
    assert error_matches(RuntimeError("boom"), StandardError) is True


def test_error_matches_refuses_a_foreign_failure_against_a_typed_shape() -> None:
    assert error_matches(RuntimeError("boom"), OutOfStock) is False


def test_error_matches_reads_a_model_payload_through_its_wire_form() -> None:
    # The payload is compared as it travels — model_dump(by_alias=True) — so a
    # catch declaring the plain dict shape still matches.
    err = DslError("out-of-stock", OutOfStock(sku="A-1", remaining=0))

    assert error_matches(err, dict[str, object]) is True


def test_error_view_rebuilds_a_dsl_error_payload_as_the_declared_type() -> None:
    err = DslError("out-of-stock", OutOfStock(sku="A-1", remaining=0))

    view = error_view(err, OutOfStock)

    assert view.code == "out-of-stock"
    assert isinstance(view.payload, OutOfStock)
    assert view.payload.sku == "A-1"


def test_error_view_projects_a_foreign_failure_onto_the_standard_shape() -> None:
    view = error_view(RuntimeError("the database is on fire"), StandardError)

    assert view.code == "INTERNAL_ERROR"
    assert isinstance(view.payload, StandardError)
    assert view.payload.code == "INTERNAL_ERROR"
    assert view.payload.message == "Internal server error"


def test_error_view_logs_only_the_foreign_failure(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.ERROR):
        error_view(DslError("out-of-stock", OutOfStock(sku="A-1", remaining=0)), OutOfStock)
    assert caplog.text == ""

    with caplog.at_level(logging.ERROR):
        error_view(RuntimeError("the database is on fire"), StandardError)
    assert "the database is on fire" in caplog.text


def test_the_whole_cluster_agrees_on_one_dsl_error_class() -> None:
    # The point of the distribution: every entry point tests the same class
    # object, so an error raised behind one boundary is recognised behind the
    # next one.
    err = DslError("already-exists", StandardError(code="already-exists", message="taken"))

    assert coerce_error(err, None).code == "already-exists"
    assert error_matches(err, StandardError) is True
    assert error_view(err, StandardError).code == "already-exists"
