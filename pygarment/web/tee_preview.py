"""Standard-library WSGI adapter for the Tee preview endpoint."""

import json
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from pygarment.serialization.geometry import GeometryInputError, serialize_geometry
from pygarment.use_cases.tee import TeeInputError, TeeRequest, generate_tee

_WSGIResponse = Callable[[str, list[tuple[str, str]]], None]


class PreviewRequestError(ValueError):
    """Raised when the HTTP request body cannot be decoded."""


def application(environ: Mapping[str, Any], start_response: _WSGIResponse) -> Iterable[bytes]:
    """Serve ``POST /api/v1/tee/preview`` as a WSGI application."""
    method = environ.get("REQUEST_METHOD", "")
    path = environ.get("PATH_INFO", "")
    if path != "/api/v1/tee/preview":
        return _json_response(
            start_response,
            "404 Not Found",
            {"error": {"code": "not_found", "message": "route not found"}},
        )
    if method != "POST":
        return _json_response(
            start_response,
            "405 Method Not Allowed",
            {"error": {"code": "method_not_allowed", "message": "POST is required"}},
        )

    try:
        request = TeeRequest.from_mapping(_read_json(environ))
        geometry = serialize_geometry(generate_tee(request)).to_mapping()
    except (PreviewRequestError, TeeInputError, GeometryInputError) as error:
        return _json_response(
            start_response,
            "400 Bad Request",
            {"error": {"code": "invalid_request", "message": str(error)}},
        )
    return _json_response(start_response, "200 OK", geometry)


def _read_json(environ: Mapping[str, Any]) -> object:
    raw_input = environ.get("wsgi.input")
    if raw_input is None:
        raise ValueError("request body is required")
    content_length = environ.get("CONTENT_LENGTH", "")
    try:
        length = int(content_length)
    except (TypeError, ValueError) as error:
        raise PreviewRequestError("content length must be an integer") from error
    if length < 0:
        raise PreviewRequestError("content length must not be negative")
    raw_body = raw_input.read(length)
    try:
        return json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PreviewRequestError("request body must contain valid JSON") from error


def _json_response(
    start_response: _WSGIResponse, status: str, payload: object
) -> Iterable[bytes]:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(encoded))),
        ],
    )
    return [encoded]


__all__ = ["application"]
