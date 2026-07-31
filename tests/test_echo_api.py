from unittest.mock import AsyncMock

import echo_api


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
    monkeypatch.setattr(echo_api.asyncio, "sleep", sleep_mock)

    response = client.get("/echo/waittime/1")

    assert response.status_code == 200
    sleep_mock.assert_awaited_once_with(1)


def test_echo_combined_path_params(client, monkeypatch):
    sleep_mock = AsyncMock()
    monkeypatch.setattr(echo_api.asyncio, "sleep", sleep_mock)

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
