from unittest.mock import AsyncMock

import header_api


def test_default_behavior_echoes_body(client):
    response = client.post("/echo/", json={"message": "hi"})

    assert response.status_code == 200
    assert response.json()["received_body"] == {"message": "hi"}


def test_statuscode_query_param_sets_response_status(client):
    response = client.get("/echo/", params={"statuscode": 204})

    assert response.status_code == 204


def test_waittime_query_param_delays_response(client, monkeypatch):
    sleep_mock = AsyncMock()
    monkeypatch.setattr(header_api.asyncio, "sleep", sleep_mock)

    response = client.get("/echo/", params={"waittime": 2})

    assert response.status_code == 200
    sleep_mock.assert_awaited_once_with(2)


def test_errorcode_query_param_triggers_500(client):
    response = client.get("/echo/", params={"errorcode": "kaputt"})

    assert response.status_code == 500
    assert response.json() == {"error": "kaputt"}
