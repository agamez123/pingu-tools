from app.main import MAX_URLS_PER_USER


def signup_and_login(client, email="user@test.com", password="pw123456", username="user"):
    client.post("/users", json={"email": email, "password": password, "username": username})
    client.post("/login", json={"email": email, "password": password})


def test_create_short_url(client):
    signup_and_login(client)

    resp = client.post("/urls", json={"original_url": "https://example.com"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["original_url"] == "https://example.com"
    assert len(body["short_code"]) > 0


def test_create_short_url_requires_login(client):
    resp = client.post("/urls", json={"original_url": "https://example.com"})

    assert resp.status_code == 401


def test_redirect_to_original_url(client):
    signup_and_login(client)
    created = client.post("/urls", json={"original_url": "https://example.com"}).json()

    resp = client.get(f"/{created['short_code']}", follow_redirects=False)

    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com"


def test_redirect_unknown_short_code_returns_404(client):
    resp = client.get("/does-not-exist")

    assert resp.status_code == 404


def test_update_url(client):
    signup_and_login(client)
    created = client.post("/urls", json={"original_url": "https://example.com"}).json()

    resp = client.post(
        f"/update/{created['short_code']}",
        data={"original_url": "https://updated.com"},
        follow_redirects=False,
    )

    assert resp.status_code == 303
    redirect = client.get(f"/{created['short_code']}", follow_redirects=False)
    assert redirect.headers["location"] == "https://updated.com"


def test_delete_url(client):
    signup_and_login(client)
    created = client.post("/urls", json={"original_url": "https://example.com"}).json()

    resp = client.delete(f"/urls/{created['short_code']}")

    assert resp.status_code == 204
    assert client.get(f"/{created['short_code']}").status_code == 404


def test_url_limit_is_enforced(client):
    signup_and_login(client)
    for _ in range(MAX_URLS_PER_USER):
        resp = client.post("/urls", json={"original_url": "https://example.com"})
        assert resp.status_code == 200

    resp = client.post("/urls", json={"original_url": "https://example.com"})

    assert resp.status_code == 403


def test_delete_all_urls(client):
    signup_and_login(client)
    codes = [
        client.post("/urls", json={"original_url": "https://example.com"}).json()["short_code"]
        for _ in range(3)
    ]

    resp = client.post("/delete-all", follow_redirects=False)

    assert resp.status_code == 303
    for code in codes:
        assert client.get(f"/{code}").status_code == 404


def test_user_cannot_delete_another_users_url(client):
    signup_and_login(client, email="owner@test.com", username="owner")
    created = client.post("/urls", json={"original_url": "https://example.com"}).json()
    client.post("/logout")

    signup_and_login(client, email="attacker@test.com", username="attacker")
    resp = client.delete(f"/urls/{created['short_code']}")

    assert resp.status_code == 404

def test_user_cannot_update_another_users_url(client):
    signup_and_login(client, email="owner@test.com", username="owner")
    created = client.post("/urls", json={"original_url": "https://example.com"}).json()
    client.post("/logout")

    signup_and_login(client, email="attacker@test.com", username="attacker")
    resp = client.delete(f"/urls/{created['short_code']}")
    client.post("/logout")

    assert resp.status_code == 404

    signup_and_login(client, email="owner@test.com", username="owner")
    check = client.get(f"/{created['short_code']}", follow_redirects=False)

    assert check.headers["location"] == "https://example.com"

def test_duplicate_email_signup_rejected(client):
    signup_and_login(client, email="dupe@test.com", username="dupe")

    resp = client.post(
        "/users",
        json={"email": "dupe@test.com", "password": "pw123456", "username": "dupe2"},
    )

    assert resp.status_code == 409


def test_login_with_wrong_password_rejected(client):
    signup_and_login(client, email="wrongpw@test.com", username="wrongpw")

    resp = client.post(
        "/login", json={"email": "wrongpw@test.com", "password": "not-the-password"}
    )

    assert resp.status_code == 401
