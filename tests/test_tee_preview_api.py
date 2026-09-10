import io
import json

import yaml

from pygarment.web.tee_preview import application


def _request_payload():
    with open("assets/bodies/mean_all.yaml", encoding="utf-8") as body_file:
        body = yaml.safe_load(body_file)["body"]
    with open("assets/design_params/t-shirt.yaml", encoding="utf-8") as design_file:
        design = yaml.safe_load(design_file)["design"]
    return {"body": body, "design": design}


def _call_app(method, path, payload=None, raw_body=None):
    body = raw_body if raw_body is not None else json.dumps(payload).encode()
    status = []
    headers = []

    def start_response(response_status, response_headers):
        status.append(response_status)
        headers.extend(response_headers)

    response = b"".join(
        application(
            {
                "REQUEST_METHOD": method,
                "PATH_INFO": path,
                "CONTENT_LENGTH": str(len(body)),
                "wsgi.input": io.BytesIO(body),
            },
            start_response,
        )
    )
    return status[0], dict(headers), json.loads(response)


def test_preview_endpoint_returns_versioned_geometry():
    status, headers, response = _call_app("POST", "/api/v1/tee/preview", _request_payload())

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json"
    assert response["version"] == "geometry.v1"
    assert response["pieces"]
    assert response["stitches"]


def test_preview_endpoint_rejects_invalid_json_contract():
    status, _, response = _call_app("POST", "/api/v1/tee/preview", {"body": None})

    assert status == "400 Bad Request"
    assert response == {
        "error": {"code": "invalid_request", "message": "request.body must be a mapping"}
    }


def test_preview_endpoint_rejects_wrong_route_or_method():
    status, _, response = _call_app("GET", "/api/v1/tee/preview", _request_payload())

    assert status == "405 Method Not Allowed"
    assert response["error"]["code"] == "method_not_allowed"


def test_preview_endpoint_returns_not_found_for_unknown_route():
    status, _, response = _call_app("POST", "/api/v1/unknown", _request_payload())

    assert status == "404 Not Found"
    assert response["error"]["code"] == "not_found"


def test_preview_endpoint_rejects_malformed_json():
    status, _, response = _call_app(
        "POST", "/api/v1/tee/preview", raw_body=b"{not-json"
    )

    assert status == "400 Bad Request"
    assert response["error"]["code"] == "invalid_request"
