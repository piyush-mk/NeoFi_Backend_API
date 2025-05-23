import pytest

def create_event_and_get_id(client, auth_headers):
    event_data = {
        "title": "Event1",
        "description": "Desc",
        "start_time": "2025-05-22T21:40:47.551Z",
        "end_time": "2025-05-22T22:40:47.551Z",
        "location": "Test",
        "is_recurring": False,
        "recurrence_pattern": {"repeat": "none"}
    }
    resp = client.post("/api/events", json=event_data, headers=auth_headers)
    assert resp.status_code == 200, f"Event creation failed: {resp.status_code}, {resp.text}"
    return resp.json()["id"]

def test_create_list_get_update_delete_event(client, auth_headers):
    event_id = create_event_and_get_id(client, auth_headers)
    resp = client.get("/api/events", headers=auth_headers)
    assert resp.status_code == 200
    assert any(e["id"] == event_id for e in resp.json())
    resp = client.get(f"/api/events/{event_id}", headers=auth_headers)
    assert resp.status_code == 200
    resp = client.put(f"/api/events/{event_id}", json={"title": "Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"
    resp = client.delete(f"/api/events/{event_id}", headers=auth_headers)
    assert resp.status_code == 200
    resp = client.get(f"/api/events/{event_id}", headers=auth_headers)
    assert resp.status_code in (403, 404)

def test_event_time_conflict(client, auth_headers):
    event_data = {
        "title": "Event1",
        "description": "Desc",
        "start_time": "2025-05-22T21:40:47.551Z",
        "end_time": "2025-05-22T22:40:47.551Z",
        "location": "Test",
        "is_recurring": False,
        "recurrence_pattern": {"repeat": "none"}
    }
    client.post("/api/events", json=event_data, headers=auth_headers)
    event_data["title"] = "Event2"
    resp = client.post("/api/events", json=event_data, headers=auth_headers)
    assert resp.status_code == 400

def test_unauthorized_event_access(client):
    resp = client.get("/api/events")
    assert resp.status_code == 401 or resp.status_code == 403
    event_data = {
        "title": "Event1",
        "description": "Desc",
        "start_time": "2025-05-22T21:40:47.551Z",
        "end_time": "2025-05-22T22:40:47.551Z",
        "location": "Test",
        "is_recurring": False,
        "recurrence_pattern": {"repeat": "none"}
    }
    resp = client.post("/api/events", json=event_data)
    assert resp.status_code == 401 or resp.status_code == 403

def test_event_not_found(client, auth_headers):
    resp = client.get("/api/events/99999", headers=auth_headers)
    assert resp.status_code in (403, 404)
    resp = client.put("/api/events/99999", json={"title": "X"}, headers=auth_headers)
    assert resp.status_code in (403, 404)
    resp = client.delete("/api/events/99999", headers=auth_headers)
    assert resp.status_code in (403, 404) 