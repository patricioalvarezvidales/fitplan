from uuid import uuid4

from fastapi.testclient import TestClient


def authenticated_headers(
    client: TestClient,
    email: str = "profile@fitplan.dev",
) -> dict[str, str]:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Usuario Perfil",
            "email": email,
            "password": "Password123",
        },
    )
    assert registration.status_code == 201

    confirmation = client.post(
        "/api/v1/auth/confirm-email",
        params={"token": registration.json()["confirmation_token"]},
    )
    assert confirmation.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Password123",
        },
    )
    assert login.status_code == 200

    return {
        "Authorization": f"Bearer {login.json()['access_token']}",
    }


def valid_profile_payload(client: TestClient) -> dict:
    catalog = client.get("/api/v1/catalog")
    assert catalog.status_code == 200

    body = catalog.json()
    assert body["equipment"]
    assert body["restrictions"]

    return {
        "age": 28,
        "gender": "masculino",
        "weight_kg": 78,
        "height_cm": 178,
        "experience_level": "intermedio",
        "primary_goal": "ganancia_muscular",
        "training_location": "gimnasio",
        "available_days": 4,
        "session_minutes": 60,
        "equipment_ids": [body["equipment"][0]["id"]],
        "restriction_ids": [body["restrictions"][0]["id"]],
    }


def test_catalog_contains_seed_data(client: TestClient) -> None:
    response = client.get("/api/v1/catalog")

    assert response.status_code == 200
    body = response.json()

    assert len(body["equipment"]) == 6
    assert len(body["restrictions"]) == 4


def test_profile_not_found_before_creation(client: TestClient) -> None:
    headers = authenticated_headers(client)

    response = client.get("/api/v1/profile", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Perfil no encontrado"


def test_create_profile_and_mark_user_complete(client: TestClient) -> None:
    headers = authenticated_headers(client)
    payload = valid_profile_payload(client)

    response = client.put(
        "/api/v1/profile",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()

    assert body["age"] == 28
    assert body["weight_kg"] == 78
    assert body["experience_level"] == "intermedio"
    assert body["primary_goal"] == "ganancia_muscular"
    assert body["available_days"] == 4
    assert set(body["equipment_ids"]) == set(payload["equipment_ids"])
    assert set(body["restriction_ids"]) == set(payload["restriction_ids"])

    profile = client.get("/api/v1/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["id"] == body["id"]

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["profile_complete"] is True


def test_update_existing_profile(client: TestClient) -> None:
    headers = authenticated_headers(
        client,
        email="profile-update@fitplan.dev",
    )
    payload = valid_profile_payload(client)

    created = client.put(
        "/api/v1/profile",
        headers=headers,
        json=payload,
    )
    assert created.status_code == 200

    payload.update(
        {
            "age": 30,
            "weight_kg": 80.5,
            "experience_level": "avanzado",
            "available_days": 5,
            "session_minutes": 75,
            "equipment_ids": [],
            "restriction_ids": [],
        }
    )

    updated = client.put(
        "/api/v1/profile",
        headers=headers,
        json=payload,
    )

    assert updated.status_code == 200
    body = updated.json()

    assert body["age"] == 30
    assert body["weight_kg"] == 80.5
    assert body["experience_level"] == "avanzado"
    assert body["available_days"] == 5
    assert body["session_minutes"] == 75
    assert body["equipment_ids"] == []
    assert body["restriction_ids"] == []


def test_invalid_catalog_references_are_rejected(
    client: TestClient,
) -> None:
    headers = authenticated_headers(
        client,
        email="invalid-catalog@fitplan.dev",
    )
    payload = valid_profile_payload(client)
    payload["equipment_ids"] = [str(uuid4())]

    response = client.put(
        "/api/v1/profile",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Equipo o restricción inválida"


def test_invalid_profile_values_return_422(client: TestClient) -> None:
    headers = authenticated_headers(
        client,
        email="invalid-profile@fitplan.dev",
    )
    payload = valid_profile_payload(client)
    payload["age"] = 15
    payload["weight_kg"] = 20
    payload["available_days"] = 1

    response = client.put(
        "/api/v1/profile",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422

    payload = valid_profile_payload(client)
    payload["experience_level"] = "experto"

    invalid_level = client.put(
        "/api/v1/profile",
        headers=headers,
        json=payload,
    )

    assert invalid_level.status_code == 422
