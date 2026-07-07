from fastapi.testclient import TestClient


def register_user(
    client: TestClient,
    email: str = "usuario@fitplan.dev",
    password: str = "Password123",
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Usuario FitPlan",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201
    return response.json()


def confirm_user(client: TestClient, confirmation_token: str) -> None:
    response = client.post(
        "/api/v1/auth/confirm-email",
        params={"token": confirmation_token},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Correo confirmado correctamente"}


def login_user(
    client: TestClient,
    email: str = "usuario@fitplan.dev",
    password: str = "Password123",
) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    return body["access_token"]


def test_register_confirm_login_me_and_logout(client: TestClient) -> None:
    registration = register_user(client)

    unconfirmed_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "usuario@fitplan.dev",
            "password": "Password123",
        },
    )
    assert unconfirmed_login.status_code == 403
    assert unconfirmed_login.json()["detail"] == (
        "Confirma tu correo antes de iniciar sesión"
    )

    confirm_user(client, registration["confirmation_token"])
    access_token = login_user(client)

    headers = {"Authorization": f"Bearer {access_token}"}

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200

    me = me_response.json()
    assert me["name"] == "Usuario FitPlan"
    assert me["email"] == "usuario@fitplan.dev"
    assert me["email_confirmed"] is True
    assert me["profile_complete"] is False

    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json() == {"message": "Sesión cerrada"}

    expired_session = client.get("/api/v1/auth/me", headers=headers)
    assert expired_session.status_code == 401
    assert expired_session.json()["detail"] == "Sesión inválida"


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    register_user(client, email="duplicate@fitplan.dev")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Segundo Usuario",
            "email": "DUPLICATE@fitplan.dev",
            "password": "Password456",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "El correo ya está registrado"


def test_invalid_registration_payloads_return_422(client: TestClient) -> None:
    invalid_email = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Usuario",
            "email": "correo-invalido",
            "password": "Password123",
        },
    )
    assert invalid_email.status_code == 422

    short_password = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Usuario",
            "email": "short@fitplan.dev",
            "password": "1234567",
        },
    )
    assert short_password.status_code == 422

    short_name = client.post(
        "/api/v1/auth/register",
        json={
            "name": "A",
            "email": "name@fitplan.dev",
            "password": "Password123",
        },
    )
    assert short_name.status_code == 422


def test_invalid_login_and_invalid_tokens(client: TestClient) -> None:
    registration = register_user(
        client,
        email="security@fitplan.dev",
        password="Password123",
    )
    confirm_user(client, registration["confirmation_token"])

    wrong_password = client.post(
        "/api/v1/auth/login",
        json={
            "email": "security@fitplan.dev",
            "password": "IncorrectPassword",
        },
    )
    assert wrong_password.status_code == 401
    assert wrong_password.json()["detail"] == (
        "Correo o contraseña incorrectos"
    )

    unknown_user = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown@fitplan.dev",
            "password": "Password123",
        },
    )
    assert unknown_user.status_code == 401

    invalid_token = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert invalid_token.status_code == 401

    confirmation_as_access = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": (
                f"Bearer {registration['confirmation_token']}"
            )
        },
    )
    assert confirmation_as_access.status_code == 401
    assert confirmation_as_access.json()["detail"] == "Token inválido"
