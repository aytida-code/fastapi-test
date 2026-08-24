def test_create_and_get_user(client):
    response = client.post(
        "/api/v1/users",
        json={"email": "jane@example.com", "full_name": "Jane Doe", "password": "supersecret123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "jane@example.com"
    assert "password" not in body

    get_response = client.get(f"/api/v1/users/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["full_name"] == "Jane Doe"


def test_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "full_name": "Dup User", "password": "supersecret123"}
    first = client.post("/api/v1/users", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/users", json=payload)
    assert second.status_code == 409


def test_get_missing_user_returns_404(client):
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404
