def test_register_and_login(client, user_data):
    # Register
    resp = client.post("/api/auth/register", json=user_data)
    assert resp.status_code == 200 or resp.status_code == 400  # 400 if already exists

    # Login
    resp = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": user_data["password"]
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert token
    headers = {"Authorization": f"Bearer {token}"}

    # Refresh token
    resp = client.post("/api/auth/refresh", headers=headers)
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # Logout (should always succeed)
    resp = client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Successfully logged out"

def test_register_duplicate(client, user_data):
    client.post("/api/auth/register", json=user_data)
    resp = client.post("/api/auth/register", json=user_data)
    assert resp.status_code == 400

def test_login_wrong_password(client, user_data):
    client.post("/api/auth/register", json=user_data)
    resp = client.post("/api/auth/login", data={
        "username": user_data["email"],
        "password": "wrongpass"
    })
    assert resp.status_code == 401 