"""Whole numbers read into ``integer`` slots.

OpenAPI defines ``integer`` by value: a JSON document may write the whole
number 100 as ``100``, ``100.0`` or ``1e2``, while ``1.5`` names no integer. The
JSON reader hands the last two spellings over as a ``float``, which
``StrictInt`` refuses, so an emitted integer slot is annotated::

    Annotated[StrictInt, BeforeValidator(runtime.whole_int)]

and an integer read from text (a path, query, header or cookie parameter)::

    Annotated[StrictInt, BeforeValidator(runtime.whole_int_text)]

Both are module-level functions rather than lambdas written at each slot, so
an emitted validator built from the annotation stays one cacheable object.
"""

from __future__ import annotations

import re
from decimal import Decimal

__all__ = ["whole_int", "whole_int_text"]

_INTEGER_TEXT = re.compile(r"^[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$")
_INTEGER_TEXT_LIMIT = Decimal(2) ** 63


def whole_int(value: object) -> object:
    """A whole ``float`` as the ``int`` it equals; anything else unchanged.

    A fractional float, a ``bool`` and a ``str`` reach ``StrictInt`` as they
    arrived and are refused there. A JSON integer arrives as an ``int`` and is
    never routed through ``float``, so it keeps every digit.
    """
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def whole_int_text(value: object) -> object:
    """The ``int`` a text spells when it spells a whole number; else unchanged.

    The text must match the shared integer spelling (sign, digits, optional
    fraction, optional exponent). Its value is computed exactly through
    ``Decimal`` and kept only when it is whole and its magnitude is at most
    2**63, so ``"1.0"`` and ``"1e2"`` give 1 and 100 while ``"1.5"`` and
    anything outside the spelling stay text for ``StrictInt`` to refuse.
    """
    if not isinstance(value, str) or _INTEGER_TEXT.fullmatch(value) is None:
        return value
    number = Decimal(value)
    # copy_abs is exact, so an exponent past the decimal context's range is
    # compared instead of raising Overflow.
    if number.copy_abs() > _INTEGER_TEXT_LIMIT or number != number.to_integral_value():
        return value
    return int(number)
