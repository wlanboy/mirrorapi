from mirror_api import hash_request


def test_hash_request_returns_none_marker_for_none():
    assert hash_request(None) == "None"


def test_hash_request_is_stable_regardless_of_key_order():
    assert hash_request({"a": 1, "b": 2}) == hash_request({"b": 2, "a": 1})


def test_hash_request_differs_for_different_data():
    assert hash_request({"a": 1}) != hash_request({"a": 2})


def _save_payload(method):
    return {
        "request": {"request_data": {"test": method}},
        "response": {"response_data": {"msg": f"Hello {method}"}, "response_status": 200},
    }


def test_save_and_lookup_roundtrip(client):
    save_response = client.post("/mirror/save", json=_save_payload("GET"))

    assert save_response.status_code == 201
    assert save_response.json() == {"message": "Request/Response pair saved."}

    lookup_response = client.post("/mirror/", json={"test": "GET"})

    assert lookup_response.status_code == 200
    assert lookup_response.json() == {"msg": "Hello GET"}


def test_save_and_lookup_with_custom_response_status(client):
    payload = {
        "request": {"request_data": {"id": 42}},
        "response": {"response_data": {"created": True}, "response_status": 201},
    }
    client.post("/mirror/save", json=payload)

    lookup_response = client.request("GET", "/mirror/", json={"id": 42})

    assert lookup_response.status_code == 201
    assert lookup_response.json() == {"created": True}


def test_save_duplicate_request_returns_conflict(client):
    payload = _save_payload("POST")
    client.post("/mirror/save", json=payload)

    response = client.post("/mirror/save", json=payload)

    assert response.status_code == 409
    assert response.json() == {
        "error": "A pair with this request, method and query already exists."
    }


def test_save_missing_fields_returns_422(client):
    response = client.post("/mirror/save", json={"request": {}})

    assert response.status_code == 422


def test_lookup_returns_404_for_unknown_request(client):
    response = client.post("/mirror/", json={"never": "saved"})

    assert response.status_code == 404
    assert response.json() == {"error": "No mirrored response found for this request."}


def test_delete_removes_saved_pair(client):
    client.post("/mirror/save", json=_save_payload("DELETE"))

    delete_response = client.post("/mirror/delete", json={"test": "DELETE"})
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Pair deleted successfully."}

    lookup_response = client.post("/mirror/", json={"test": "DELETE"})
    assert lookup_response.status_code == 404


def test_delete_returns_404_for_unknown_pair(client):
    response = client.post("/mirror/delete", json={"never": "saved"})

    assert response.status_code == 404
    assert response.json() == {"error": "No matching pair found to delete."}


def test_list_returns_empty_list_when_nothing_saved(client):
    response = client.get("/mirror/list")

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_saved_pairs(client):
    client.post("/mirror/save", json=_save_payload("GET"))
    client.post("/mirror/save", json=_save_payload("POST"))

    response = client.get("/mirror/list")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 2
    assert {"request_data", "response_data", "response_status", "id"} <= entries[0].keys()
    assert {e["request_data"]["test"] for e in entries} == {"GET", "POST"}


def test_list_no_longer_includes_deleted_pair(client):
    client.post("/mirror/save", json=_save_payload("DELETE"))
    client.post("/mirror/delete", json={"test": "DELETE"})

    response = client.get("/mirror/list")

    assert response.status_code == 200
    assert response.json() == []


def test_same_body_different_methods_do_not_collide(client):
    same_body = {"user_id": 123}
    client.post("/mirror/save", json={
        "request": {"request_data": same_body, "method": "GET"},
        "response": {"response_data": {"action": "get"}, "response_status": 200},
    })
    client.post("/mirror/save", json={
        "request": {"request_data": same_body, "method": "POST"},
        "response": {"response_data": {"action": "post"}, "response_status": 201},
    })

    get_response = client.request("GET", "/mirror/", json=same_body)
    post_response = client.post("/mirror/", json=same_body)

    assert get_response.status_code == 200
    assert get_response.json() == {"action": "get"}
    assert post_response.status_code == 201
    assert post_response.json() == {"action": "post"}


def test_same_body_different_query_params_do_not_collide(client):
    same_body = {"user_id": 123}
    client.post("/mirror/save", json={
        "request": {"request_data": same_body, "query_params": {"expand": "profile"}},
        "response": {"response_data": {"expanded": True}, "response_status": 200},
    })
    client.post("/mirror/save", json={
        "request": {"request_data": same_body, "query_params": {"expand": "none"}},
        "response": {"response_data": {"expanded": False}, "response_status": 200},
    })

    profile_response = client.post("/mirror/?expand=profile", json=same_body)
    none_response = client.post("/mirror/?expand=none", json=same_body)

    assert profile_response.json() == {"expanded": True}
    assert none_response.json() == {"expanded": False}


def test_wildcard_pair_matches_any_method_as_fallback(client):
    same_body = {"user_id": 7}
    client.post("/mirror/save", json={
        "request": {"request_data": same_body},
        "response": {"response_data": {"action": "any"}, "response_status": 200},
    })
    client.post("/mirror/save", json={
        "request": {"request_data": same_body, "method": "DELETE"},
        "response": {"response_data": {"action": "delete"}, "response_status": 200},
    })

    get_response = client.request("GET", "/mirror/", json=same_body)
    delete_response = client.request("DELETE", "/mirror/", json=same_body)

    assert get_response.json() == {"action": "any"}
    assert delete_response.json() == {"action": "delete"}


def test_save_same_body_and_method_twice_returns_conflict(client):
    payload = {
        "request": {"request_data": {"a": 1}, "method": "GET"},
        "response": {"response_data": {"msg": "hi"}, "response_status": 200},
    }
    client.post("/mirror/save", json=payload)

    response = client.post("/mirror/save", json=payload)

    assert response.status_code == 409


def test_list_shows_method_and_query_params(client):
    client.post("/mirror/save", json={
        "request": {"request_data": {"a": 1}, "method": "GET", "query_params": {"x": "1"}},
        "response": {"response_data": {"msg": "hi"}, "response_status": 200},
    })

    entries = client.get("/mirror/list").json()

    assert entries[0]["method"] == "GET"
    assert entries[0]["query_params"] == {"x": "1"}


def test_delete_removes_all_method_variants_for_a_body(client):
    same_body = {"user_id": 99}
    client.post("/mirror/save", json={
        "request": {"request_data": same_body, "method": "GET"},
        "response": {"response_data": {"action": "get"}, "response_status": 200},
    })
    client.post("/mirror/save", json={
        "request": {"request_data": same_body, "method": "POST"},
        "response": {"response_data": {"action": "post"}, "response_status": 200},
    })

    delete_response = client.post("/mirror/delete", json=same_body)
    assert delete_response.status_code == 200

    assert client.request("GET", "/mirror/", json=same_body).status_code == 404
    assert client.post("/mirror/", json=same_body).status_code == 404


def test_delete_returns_400_for_invalid_json_body(client):
    response = client.post(
        "/mirror/delete",
        content=b"not json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json() == {"error": "Invalid JSON in request body."}
