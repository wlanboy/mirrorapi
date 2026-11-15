import asyncio
from unittest.mock import AsyncMock

import pytest

import request_control


def test_echo_returns_json_body(client):
    response = client.post("/echo/statuscode/200", json={"body": "Hallo Echo"})

    assert response.status_code == 200
    assert response.json()["received_body"] == {"body": "Hallo Echo"}


def test_echo_returns_custom_status_code_from_path(client):
    response = client.get("/echo/statuscode/201")

    assert response.status_code == 201


def test_echo_returns_error_message_from_path(client):
    response = client.get("/echo/errorcode/kaputt")

    assert response.status_code == 500
    assert response.json() == {"error": "kaputt"}


def test_echo_combines_statuscode_and_errorcode_from_path(client):
    response = client.get("/echo/statuscode/500/errorcode/Path-based-error")

    assert response.status_code == 500
    assert response.json() == {"error": "Path-based-error"}


def test_echo_returns_status_code_from_header_fallback(client):
    response = client.get("/echo/test", headers={"request-statuscode": "202"})

    assert response.status_code == 202


def test_echo_waits_before_responding(client, monkeypatch):
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)

    response = client.get("/echo/waittime/1")

    assert response.status_code == 200
    sleep_mock.assert_awaited_once_with(1)


def test_echo_combined_path_params(client, monkeypatch):
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)

    response = client.get("/echo/statuscode/204/waittime/2")

    assert response.status_code == 204
    sleep_mock.assert_awaited_once_with(2)


def test_echo_returns_400_for_invalid_statuscode_header(client):
    response = client.get("/echo/test", headers={"request-statuscode": "abc"})

    assert response.status_code == 400
    assert response.json() == {
        "error": "Invalid value for request-statuscode, must be an integer."
    }


def test_echo_returns_400_for_invalid_waittime_header(client):
    response = client.get("/echo/test", headers={"request-waittime": "abc"})

    assert response.status_code == 400
    assert response.json() == {
        "error": "Invalid value for request-waittime, must be an integer."
    }


def test_echo_echoes_back_custom_header(client):
    response = client.get("/echo/test", headers={"X-Custom": "foobar"})

    assert response.status_code == 200
    assert response.headers["x-custom"] == "foobar"


def test_echo_does_not_override_response_content_type(client):
    response = client.post(
        "/echo/statuscode/200",
        content=b"plain text body",
        headers={"content-type": "text/plain"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


def test_echo_returns_plain_text_body(client):
    response = client.post(
        "/echo/statuscode/200",
        content=b"plain text body",
        headers={"content-type": "text/plain"},
    )

    assert response.status_code == 200
    assert response.json()["received_body"] == "plain text body"


def test_echo_does_not_mirror_content_encoding(client):
    response = client.post(
        "/echo/test",
        json={"body": "unkomprimiert"},
        headers={"Content-Encoding": "gzip", "X-Custom": "bleibt"},
    )

    assert response.status_code == 200
    assert "content-encoding" not in response.headers
    assert response.headers["x-custom"] == "bleibt"


def test_echo_does_not_mirror_hop_by_hop_headers(client):
    response = client.get(
        "/echo/test",
        headers={"TE": "trailers", "Upgrade": "h2c", "Keep-Alive": "timeout=5", "Proxy-Authorization": "Basic x"},
    )

    assert response.status_code == 200
    for name in ("te", "upgrade", "keep-alive", "proxy-authorization"):
        assert name not in response.headers


@pytest.mark.parametrize("status", ["1000", "-5", "100", "199", "600"])
def test_echo_rejects_status_code_out_of_range(client, status):
    response = client.get(f"/echo/statuscode/{status}")

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid value for statuscode, must be between 200 and 599."}


def test_echo_rejects_header_status_code_out_of_range(client):
    response = client.get("/echo/test", headers={"request-statuscode": "1000"})

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid value for request-statuscode, must be between 200 and 599."}


@pytest.mark.parametrize("status", [204, 304])
def test_echo_sends_empty_body_for_no_content_status(client, status):
    response = client.get(f"/echo/statuscode/{status}", headers={"X-Custom": "bleibt"})

    assert response.status_code == status
    assert response.content == b""
    assert "content-type" not in response.headers
    assert response.headers["x-custom"] == "bleibt"


def test_echo_rejects_waittime_above_maximum(client, monkeypatch):
    monkeypatch.setattr(request_control, "MAX_WAIT_SECONDS", 10)
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)

    response = client.get("/echo/waittime/11")

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid value for waittime, must be between 0 and 10."}
    sleep_mock.assert_not_awaited()


def test_echo_accepts_waittime_at_maximum(client, monkeypatch):
    monkeypatch.setattr(request_control, "MAX_WAIT_SECONDS", 10)
    sleep_mock = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep_mock)

    response = client.get("/echo/test", headers={"request-waittime": "10"})

    assert response.status_code == 200
    sleep_mock.assert_awaited_once_with(10)


def test_echo_rejects_negative_waittime(client):
    response = client.get("/echo/waittime/-1")

    assert response.status_code == 400
