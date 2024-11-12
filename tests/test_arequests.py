import json

import pytest

import rio.arequests as arequests


def test_http_response_invalid_json() -> None:
    response = arequests.HttpResponse(
        status_code=200,
        headers={},
        content=b"invalid json",
    )

    with pytest.raises(json.JSONDecodeError, match="Expecting value"):
        response.json()


def test_http_response_invalid_utf8() -> None:
    response = arequests.HttpResponse(
        status_code=200,
        headers={},
        content=b"\xff",
    )

    with pytest.raises(json.JSONDecodeError, match="UTF-8"):
        response.json()


def test_request() -> None:
    response = arequests.request_sync(
        "get",
        "https://postman-echo.com/get",
        json={"foo": "bar"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json; charset=utf-8"

    response_json = response.json()

    assert response_json["headers"]["user-agent"] == "rio.arequests/0.1"
    assert response_json["headers"]["host"] == "postman-echo.com"
    assert response_json["headers"]["content-type"] == "application/json"
    assert response_json["headers"]["content-length"] == "14"
    assert response_json["args"] == {"foo": "bar"}
