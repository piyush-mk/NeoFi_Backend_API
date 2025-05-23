import pytest

def create_event_and_get_id(client, auth_headers):
    event_data = {
        "title": "VersionEvent",
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

def test_get_event_version_and_diff(client, auth_headers):
    event_id = create_event_and_get_id(client, auth_headers)
    client.put(f"/api/events/{event_id}", json={"title": "V2"}, headers=auth_headers)
    resp = client.get(f"/api/events/{event_id}/history/1", headers=auth_headers)
    assert resp.status_code == 200
    resp = client.get(f"/api/events/{event_id}/history/2", headers=auth_headers)
    assert resp.status_code == 200
    resp = client.get(f"/api/events/{event_id}/diff/1/2", headers=auth_headers)
    assert resp.status_code == 200
    diffs = resp.json()
    assert any(d["field_name"] == "title" for d in diffs)

def test_rollback_event(client, auth_headers):
    event_id = create_event_and_get_id(client, auth_headers)
    client.put(f"/api/events/{event_id}", json={"title": "V2"}, headers=auth_headers)
    resp = client.post(f"/api/events/{event_id}/rollback/1", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "VersionEvent"

def test_version_not_found(client, auth_headers):
    event_id = create_event_and_get_id(client, auth_headers)
    resp = client.get(f"/api/events/{event_id}/history/99999", headers=auth_headers)
    assert resp.status_code == 404
    resp = client.get(f"/api/events/{event_id}/diff/1/99999", headers=auth_headers)
    assert resp.status_code == 404
    resp = client.post(f"/api/events/{event_id}/rollback/99999", headers=auth_headers)
    assert resp.status_code == 404 