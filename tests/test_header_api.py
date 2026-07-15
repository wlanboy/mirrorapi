from unittest.mock import AsyncMock

import header_api


def test_default_behavior_echoes_body_and_headers(client):
    response = client.post(
        "/request/",
        json={"message": "Hello from test"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["received_body"] == {"message": "Hello from test"}
    assert data["received_headers"]["content-type"] == "application/json"


def test_statuscode_header_sets_response_status(client):
    response = client.get("/request/", headers={"request-statuscode": "201"})

    assert response.status_code == 201


def test_waittime_header_delays_response(client, monkeypatch):
    sleep_mock = AsyncMock()
    monkeypatch.setattr(header_api.asyncio, "sleep", sleep_mock)

    response = client.get("/request/", headers={"request-waittime": "3"})

    assert response.status_code == 200
    sleep_mock.assert_awaited_once_with(3)


def test_errorcode_header_triggers_500(client):
    response = client.post(
        "/request/",
        json={"operation": "critical_task"},
        headers={"request-errorcode": "Invalid data provided"},
    )

    assert response.status_code == 500
    assert response.json() == {"error": "Invalid data provided"}


def test_plain_text_body_is_echoed(client):
    response = client.post(
        "/request/",
        content=b"plain text body",
        headers={"content-type": "text/plain"},
    )

    assert response.status_code == 200
    assert response.json()["received_body"] == "plain text body"
