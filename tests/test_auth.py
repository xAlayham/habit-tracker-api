def test_register_creates_user(client):
    res = client.post("/users/register", json={"username": "newuser", "password": "supersecret"})

    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "newuser"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_username_rejected(client):
    client.post("/users/register", json={"username": "dupe", "password": "supersecret"})
    res = client.post("/users/register", json={"username": "dupe", "password": "anotherpass"})

    assert res.status_code == 400
    assert res.json()["detail"] == "Username already taken"


def test_register_username_too_short_rejected(client):
    res = client.post("/users/register", json={"username": "ab", "password": "supersecret"})
    assert res.status_code == 422


def test_register_password_too_short_rejected(client):
    res = client.post("/users/register", json={"username": "someuser", "password": "short"})
    assert res.status_code == 422


def test_login_success_returns_bearer_token(client):
    client.post("/users/register", json={"username": "loginuser", "password": "supersecret"})
    res = client.post("/users/login", data={"username": "loginuser", "password": "supersecret"})

    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_rejected(client):
    client.post("/users/register", json={"username": "loginuser2", "password": "supersecret"})
    res = client.post("/users/login", data={"username": "loginuser2", "password": "wrongpass"})

    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid username or password"


def test_login_nonexistent_user_rejected(client):
    res = client.post("/users/login", data={"username": "ghost", "password": "whatever1"})

    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid username or password"


def test_protected_route_rejects_missing_token(client):
    res = client.get("/habits")
    assert res.status_code == 401


def test_protected_route_rejects_garbage_token(client):
    res = client.get("/habits", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_protected_route_accepts_valid_token(client, auth_headers):
    res = client.get("/habits", headers=auth_headers)
    assert res.status_code == 200
