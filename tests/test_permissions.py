import pytest

def create_event_and_get_id(client, auth_headers):
    event_data = {
        "title": "PermEvent",
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

@pytest.fixture
def second_user(client):
    data = {"email": "second@example.com", "username": "second", "password": "secondpass"}
    client.post("/api/auth/register", json=data)
    resp = client.post("/api/auth/login", data={"username": data["email"], "password": data["password"]})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, data

def test_share_list_update_delete_permission(client, auth_headers, second_user):
    second_headers, second_data = second_user
    event_id = create_event_and_get_id(client, auth_headers)
    resp = client.post(f"/api/events/{event_id}/share", json={"user_id": 2, "role": "editor"}, headers=auth_headers)
    assert resp.status_code == 200
    perm_id = resp.json()["id"]
    resp = client.get(f"/api/events/{event_id}/permissions", headers=auth_headers)
    assert resp.status_code == 200
    assert any(p["id"] == perm_id for p in resp.json())
    resp = client.put(f"/api/events/{event_id}/permissions/2", json={"role": "viewer"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["role"] == "viewer"
    resp = client.delete(f"/api/events/{event_id}/permissions/2", headers=auth_headers)
    assert resp.status_code == 200

def test_duplicate_permission(client, auth_headers, second_user):
    second_headers, second_data = second_user
    event_id = create_event_and_get_id(client, auth_headers)
    client.post(f"/api/events/{event_id}/share", json={"user_id": 2, "role": "editor"}, headers=auth_headers)
    resp = client.post(f"/api/events/{event_id}/share", json={"user_id": 2, "role": "editor"}, headers=auth_headers)
    assert resp.status_code == 400

def test_permission_not_found(client, auth_headers):
    event_id = create_event_and_get_id(client, auth_headers)
    resp = client.put(f"/api/events/{event_id}/permissions/99999", json={"role": "viewer"}, headers=auth_headers)
    assert resp.status_code == 404
    resp = client.delete(f"/api/events/{event_id}/permissions/99999", headers=auth_headers)
    assert resp.status_code == 404

def test_permission_forbidden(client, second_user):
    second_headers, _ = second_user
    resp = client.post(f"/api/events/99999/share", json={"user_id": 1, "role": "editor"}, headers=second_headers)
    assert resp.status_code in (403, 404) 