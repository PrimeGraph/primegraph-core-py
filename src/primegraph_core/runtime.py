"""The shared vocabulary under the qualifier emitted code already writes.

Every emitted reference to a shared declaration is qualified — ``runtime.File``,
``runtime.DslErrorView[...]``, ``runtime.error_matches(...)`` — so the cheapest
correct import for a generated module is one that keeps that qualifier::

    from primegraph_core import runtime

The name ``runtime`` is bound locally by that statement; it is not a top-level
distribution package, so two generated distributions can both write it without
one shadowing the other on ``sys.path``.
"""

from primegraph_core import (
    DSL_ERROR_MESSAGES,
    TRANSPORT_ERROR_CODES,
    DslError,
    DslErrorView,
    File,
    coerce_error,
    default_error_message,
    error_matches,
    error_view,
    transport_error_code,
)

__all__ = [
    "DSL_ERROR_MESSAGES",
    "TRANSPORT_ERROR_CODES",
    "DslError",
    "DslErrorView",
    "File",
    "coerce_error",
    "default_error_message",
    "error_matches",
    "error_view",
    "transport_error_code",
]
