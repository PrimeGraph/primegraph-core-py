"""What one outbound HTTP call returned.

Only the value type lives here. The transport that fills it — ``fetch``, the
auth application, the response decode — is per-bundle machinery and stays in the
generated package. ``HttpResponse`` carries no behaviour at all and every
generated package that emits an HTTP step repeated it verbatim, so it is
declared once and re-exported under the ``runtime`` qualifier emitted code
already writes.

There is no request type beside it: the Python transport takes the request as a
plain mapping, so a step builds a dict literal and nothing names a class.
"""

from __future__ import annotations

__all__ = ["HttpResponse"]


# Plain and ``__slots__``-ed rather than a pydantic model: nothing validates a
# response carrier, nothing puts one on the wire, and a step reads it straight
# after the call. The three members are positional because that is how the
# transport constructs it.
class HttpResponse:
    __slots__ = ("status", "headers", "body")

    status: int
    headers: dict[str, str]
    body: bytes

    def __init__(self, status: int, headers: dict[str, str], body: bytes) -> None:
        self.status = status
        self.headers = headers
        self.body = body
