"""``HttpResponse`` — the three members a step reads off a finished call."""

from __future__ import annotations

import pytest

from primegraph_core import HttpResponse


def test_constructs_positionally_the_way_the_transport_does() -> None:
    # The generated `fetch` builds it positionally, so the parameter ORDER is
    # the contract just as much as the names are.
    resp = HttpResponse(201, {"content-type": "application/json"}, b'{"ok":true}')

    assert resp.status == 201
    assert resp.headers == {"content-type": "application/json"}
    assert resp.body == b'{"ok":true}'


def test_constructs_by_name_too() -> None:
    resp = HttpResponse(status=404, headers={}, body=b"")

    assert resp.status == 404
    assert resp.headers == {}
    assert resp.body == b""


def test_the_body_stays_the_bytes_that_arrived() -> None:
    # A typed body is what the step's declared response schemas are for; the
    # carrier decodes nothing.
    raw = "ünïcode".encode("utf-8")
    resp = HttpResponse(200, {}, raw)

    assert resp.body is raw


def test_the_members_are_slotted_so_a_typo_is_reported() -> None:
    # `__slots__` is why a misspelled member fails loudly instead of silently
    # attaching a new attribute nothing will ever read.
    resp = HttpResponse(200, {}, b"")

    assert not hasattr(resp, "__dict__")
    with pytest.raises(AttributeError):
        resp.stauts = 200  # type: ignore[attr-defined]
