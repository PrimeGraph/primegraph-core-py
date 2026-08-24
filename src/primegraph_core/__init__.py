"""Shared cross-package vocabulary for PrimeGraph generated Python packages.

The module is deliberately named ``primegraph_core`` and not ``runtime``: a
generic top-level name collides as soon as two distributions are installed into
one environment, and every generated package of a graph shares that
environment. Nothing here is ever exposed at top level under a generic name —
``primegraph_core.runtime`` is a submodule, so the qualifier ``runtime`` that
emitted code already writes stays available without any distribution claiming
the top-level name.

What lives here is only what has to be one object per process:

* :class:`~primegraph_core.files.File` — pydantic validates a ``BaseModel``
  typed field by ``isinstance``, so a second copy of the class makes a model in
  one package reject a file built by another with a ``ValidationError``.
* :class:`~primegraph_core.errors.DslError` and everything that reaches
  ``isinstance(e, DslError)`` — with two copies a raised DSL error degrades to
  ``INTERNAL_ERROR`` and drops its typed payload, silently.

* :class:`~primegraph_core.http.HttpResponse` — not by identity, but because it
  is pure declaration: every generated package repeated the same three members
  and none of them ever differed.

Everything else the compiler emits — the expression helpers, the HTTP and
Firebase transport, ``validate_schema``, ``fetch``, ``parse_response`` — stays
inside the generated packages. Those raise ``DslError`` but nothing tests their
identity, so a copy per package costs nothing.
"""

from primegraph_core.errors import (
    DSL_ERROR_MESSAGES,
    TRANSPORT_ERROR_CODES,
    DslError,
    DslErrorView,
    coerce_error,
    default_error_message,
    error_matches,
    error_view,
    transport_error_code,
)
from primegraph_core.files import File
from primegraph_core.http import HttpResponse

__all__ = [
    "DSL_ERROR_MESSAGES",
    "TRANSPORT_ERROR_CODES",
    "DslError",
    "DslErrorView",
    "File",
    "HttpResponse",
    "coerce_error",
    "default_error_message",
    "error_matches",
    "error_view",
    "transport_error_code",
]
