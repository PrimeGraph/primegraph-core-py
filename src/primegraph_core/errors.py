"""The DSL error vocabulary that has to be one nominal type per graph.

Every boundary in the generated code recognises a DSL error by
``isinstance(e, DslError)``. Split across two published distributions, that test
is ``False`` between them, so a raised error silently degrades to
``INTERNAL_ERROR`` and its typed payload is discarded — no exception, no log,
just the wrong code on the wire. So ``DslError``, the view it is projected onto,
and every function that reaches that ``isinstance`` live here, in one place, and
the generated packages import them.

``validate_schema``, ``fetch`` and ``parse_response`` stay inside the generated
packages: they *raise* ``DslError`` but nothing tests their identity, so a copy
per package is harmless. They import ``DslError`` from here.
"""

from __future__ import annotations

import importlib
import logging
from functools import lru_cache
from types import ModuleType
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError

__all__ = [
    "DSL_ERROR_MESSAGES",
    "TRANSPORT_ERROR_CODES",
    "DslError",
    "DslErrorView",
    "coerce_error",
    "default_error_message",
    "error_matches",
    "error_view",
    "transport_error_code",
]

T = TypeVar("T")


class DslError(Exception, Generic[T]):
    __slots__ = ('code', 'payload')

    def __init__(self, code: str, payload: T):
        super().__init__(code)
        self.code = code
        self.payload = payload


class DslErrorView(Generic[T]):
    __slots__ = ('code', 'payload')

    def __init__(self, code: str, payload: T):
        self.code = code
        self.payload = payload

    def to_json(self) -> dict[str, Any]:
        # json.dumps cannot serialize this class directly; string()/json.marshal
        # on the error view route through its {code, payload} dict.
        return {'code': self.code, 'payload': self.payload}


# Default text of each error code. A coerced error has no message of its own —
# a foreign SDK's wording never reaches a client — so a text payload slot it
# leaves empty is filled from here, and the error view always carries a code
# AND a message.
DSL_ERROR_MESSAGES: dict[str, str] = {
    'AUTH_REQUIRED': 'Authorization required',
    'VALIDATION_FAILED': 'Request validation failed',
    'INTERNAL_ERROR': 'Internal server error',
    'NOT_FOUND': 'Resource not found',
    'METHOD_NOT_ALLOWED': 'Method not allowed',
    'FORBIDDEN': 'Access forbidden',
    'NO_RESPONSE': 'Block did not produce a response',
    'invalid-argument': 'Invalid argument',
    'failed-precondition': 'Failed precondition',
    'out-of-range': 'Value out of range',
    'unauthenticated': 'Authorization required',
    'permission-denied': 'Access forbidden',
    'not-found': 'Resource not found',
    'already-exists': 'Resource already exists',
    'resource-exhausted': 'Resource exhausted',
    'cancelled': 'Request cancelled',
    'data-loss': 'Data loss',
    'unknown': 'Unknown error',
    'internal': 'Internal server error',
    'unavailable': 'Service unavailable',
    'deadline-exceeded': 'Deadline exceeded',
    'aborted': 'Operation aborted',
    'UNSUPPORTED_MEDIA_TYPE': 'Unsupported media type',
    'UTF8_DECODE_FAILED': 'Input is not valid UTF-8',
    'BASE64_DECODE_FAILED': 'Input is not valid base64',
    'HEX_DECODE_FAILED': 'Input is not valid hex',
    'URL_DECODE_FAILED': 'Input is not valid percent-encoded text',
    'ENUM_VALUE_NOT_A_MEMBER': 'Value is not a member of the enumeration',
    'JSON_PARSE_FAILED': 'Input is not valid JSON',
    'DECIMAL_PARSE_FAILED': 'Input is not a decimal number',
    'DURATION_PARSE_FAILED': 'Input is not a valid duration',
    'TIME_PARSE_FAILED': 'Input does not match the expected time format',
}


def default_error_message(code: str) -> str:
    return DSL_ERROR_MESSAGES.get(code, 'Internal server error')


def _coerced_payload(code: str, default_payload: Any) -> Any:
    if isinstance(default_payload, str) and default_payload == '':
        return default_error_message(code)
    return default_payload


# The real firebase-admin / google-api-core exception surface. Either
# library may be absent from a bundle that never calls it, so the import
# degrades to None and the isinstance guard below never matches. The
# resolver types that degradation, so the fallback needs no retyping of
# an imported name.
def _optional_module(name: str) -> ModuleType | None:
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


_gapi_exceptions = _optional_module('google.api_core.exceptions')
_fbadmin_exceptions = _optional_module('firebase_admin.exceptions')


# Status name -> DSL kebab code. Firestore and the other google-cloud
# surfaces raise GoogleAPICallError with a grpc status; firebase-admin
# raises FirebaseError whose code is the same UPPER_SNAKE name, or CONFLICT
# for a bare 409. Mapping both into the DSL code space lets a catch on
# err.code == 'already-exists' match whichever SDK produced the failure.
TRANSPORT_ERROR_CODES: dict[str, str] = {
    'INVALID_ARGUMENT': 'invalid-argument',
    'FAILED_PRECONDITION': 'failed-precondition',
    'OUT_OF_RANGE': 'out-of-range',
    'UNAUTHENTICATED': 'unauthenticated',
    'PERMISSION_DENIED': 'permission-denied',
    'NOT_FOUND': 'not-found',
    'ALREADY_EXISTS': 'already-exists',
    'RESOURCE_EXHAUSTED': 'resource-exhausted',
    'CANCELLED': 'cancelled',
    'DATA_LOSS': 'data-loss',
    'UNKNOWN': 'unknown',
    'INTERNAL': 'internal',
    'UNAVAILABLE': 'unavailable',
    'DEADLINE_EXCEEDED': 'deadline-exceeded',
    'ABORTED': 'aborted',
    'CONFLICT': 'aborted',
}


def transport_error_code(e: BaseException) -> str | None:
    # The DSL code a raw SDK failure presents, None when nothing names it.
    if _gapi_exceptions is not None and isinstance(e, _gapi_exceptions.GoogleAPICallError):
        grpc_status = e.grpc_status_code
        if grpc_status is not None:
            return TRANSPORT_ERROR_CODES.get(grpc_status.name, 'unknown')
    if _fbadmin_exceptions is not None and isinstance(e, _fbadmin_exceptions.FirebaseError):
        return TRANSPORT_ERROR_CODES.get(e.code, 'unknown')
    return None


def coerce_error(e: Exception, default_payload: Any) -> DslErrorView[Any]:
    # Projects ANY caught error onto the catch binding {code, payload}. A DSL
    # raise yields its own code + typed payload; a raw SDK failure is named in
    # the DSL code space by transport_error_code, so a catch on
    # err.code == 'already-exists' matches; any other error becomes code
    # 'INTERNAL_ERROR' with the default payload of the catch's declared type.
    if isinstance(e, DslError):
        return DslErrorView(e.code, e.payload)
    # A foreign error carries no typed payload, so its own text would be lost
    # here. It goes to the log instead of the returned view: the code is what a
    # caller may put on the wire, the text stays server-side.
    mapped = transport_error_code(e)
    code = 'INTERNAL_ERROR' if mapped is None else mapped
    logging.getLogger(__name__).error('[dsl] error coerced to %s: %s', code, e)
    return DslErrorView(code, _coerced_payload(code, default_payload))


# A private adapter cache, not a shared contract: `validate_schema` keeps its own
# copy inside each generated package. Caching a TypeAdapter is a per-process
# convenience with no cross-package identity to preserve, so the duplicate is
# harmless — unlike DslError, where two copies are the bug.
@lru_cache(maxsize=None)
def _schema_validator(declared: Any) -> TypeAdapter[Any]:
    return TypeAdapter(declared)


def _wire_form(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode='json', by_alias=True)
    if isinstance(value, list):
        return [_wire_form(v) for v in value]
    if isinstance(value, dict):
        return {k: _wire_form(v) for k, v in value.items()}
    return value


def _arrived_error(e: Exception) -> tuple[str, Any]:
    if isinstance(e, DslError):
        return e.code, _wire_form(e.payload)
    # A foreign failure carries no payload of its own, so what arrives is the
    # standard error object — named in the DSL code space by the same transport
    # coercion coerce_error consults, so a catch on err.code == 'already-exists'
    # matches whichever SDK produced the failure. A failure nothing names stays
    # INTERNAL_ERROR.
    mapped = transport_error_code(e)
    code = 'INTERNAL_ERROR' if mapped is None else mapped
    return code, {'code': code, 'message': default_error_message(code)}


def error_matches(e: Exception, declared: Any) -> bool:
    # A catch handles an error when the arrived payload satisfies the schema the
    # catch declared, never by the class the error was raised as.
    try:
        _schema_validator(declared).validate_python(_arrived_error(e)[1])
    except ValidationError:
        return False
    return True


def error_view(e: Exception, declared: Any) -> DslErrorView[Any]:
    code, arrived = _arrived_error(e)
    if not isinstance(e, DslError):
        logging.getLogger(__name__).error('[dsl] error coerced to %s: %s', code, e)
    # Rebuilt as the declared type, so a rich format arrives as its carrier
    # rather than as the text it travelled on.
    return DslErrorView(code, _schema_validator(declared).validate_python(arrived))
