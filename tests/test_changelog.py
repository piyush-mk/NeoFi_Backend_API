def create_event_and_get_id(client, auth_headers):
    event_data = {
        "title": "ChangelogEvent",
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

def test_get_event_changelog(client, auth_headers):
    event_id = create_event_and_get_id(client, auth_headers)
    client.put(f"/api/events/{event_id}", json={"title": "ChangedTitle"}, headers=auth_headers)
    resp = client.get(f"/api/events/{event_id}/changelog", headers=auth_headers)
    assert resp.status_code == 200
    changelog = resp.json()
    assert len(changelog) > 0
    assert any(c["field_name"] == "title" for c in changelog)
    for entry in changelog:
        assert entry["version_id"] is not None
        assert isinstance(entry["version_id"], int)

def test_changelog_not_found(client, auth_headers):
    resp = client.get("/api/events/99999/changelog", headers=auth_headers)
    assert resp.status_code in (403, 404) 