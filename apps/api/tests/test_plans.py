from fastapi.testclient import TestClient


def authenticated_headers(
    client: TestClient,
    email: str,
) -> dict[str, str]:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Usuario Planes",
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


def create_profile(
    client: TestClient,
    headers: dict[str, str],
    available_days: int = 2,
) -> dict:
    catalog = client.get("/api/v1/catalog")
    assert catalog.status_code == 200

    equipment_ids = [
        item["id"]
        for item in catalog.json()["equipment"]
    ]

    payload = {
        "age": 28,
        "gender": "masculino",
        "weight_kg": 78,
        "height_cm": 178,
        "experience_level": "intermedio",
        "primary_goal": "ganancia_muscular",
        "training_location": "gimnasio",
        "available_days": available_days,
        "session_minutes": 45,
        "equipment_ids": equipment_ids,
        "restriction_ids": [],
    }

    response = client.put(
        "/api/v1/profile",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 200

    return response.json()


def generate_plan(
    client: TestClient,
    headers: dict[str, str],
) -> dict:
    response = client.post(
        "/api/v1/plans/generate",
        headers=headers,
    )
    assert response.status_code == 200

    return response.json()


def completion_payload(
    session: dict,
    difficulty: int = 6,
    energy_level: int = 8,
    pain_reported: bool = False,
) -> dict:
    return {
        "actual_minutes": session["estimated_minutes"],
        "difficulty": difficulty,
        "energy_level": energy_level,
        "satisfaction": 9,
        "pain_reported": pain_reported,
        "pain_area": "espalda" if pain_reported else "",
        "comments": "Prueba automática FitPlan",
        "exercises": [
            {
                "session_exercise_id": item["id"],
                "actual_weight_kg": item["recommended_weight_kg"],
                "completed_sets": item["sets"],
                "completed_repetitions": item["repetitions"],
            }
            for item in session["exercises"]
        ],
    }


def find_exercise(
    plan: dict,
    exercise_id: str,
) -> dict | None:
    for session in plan["sessions"]:
        for item in session["exercises"]:
            if item["exercise"]["id"] == exercise_id:
                return item
    return None


def find_external_exercise(plan: dict) -> tuple[dict, dict]:
    for session in plan["sessions"]:
        for item in session["exercises"]:
            if (
                item["exercise"]["load_type"] == "external"
                and item["recommended_weight_kg"] > 0
            ):
                return session, item

    raise AssertionError(
        "La rutina no contiene un ejercicio externo con carga"
    )


def test_plan_requires_completed_profile(
    client: TestClient,
) -> None:
    headers = authenticated_headers(
        client,
        "without-profile@fitplan.dev",
    )

    generate = client.post(
        "/api/v1/plans/generate",
        headers=headers,
    )
    assert generate.status_code == 400
    assert generate.json()["detail"] == (
        "Completa tu perfil antes de generar una rutina"
    )

    current = client.get(
        "/api/v1/plans/current",
        headers=headers,
    )
    assert current.status_code == 404


def test_generate_list_and_preserve_week_history(
    client: TestClient,
) -> None:
    headers = authenticated_headers(
        client,
        "weeks@fitplan.dev",
    )
    create_profile(client, headers)

    first_plan = generate_plan(client, headers)

    assert first_plan["version"] == 1
    assert first_plan["status"] == "active"
    assert len(first_plan["sessions"]) == 2
    assert all(
        len(session["exercises"]) >= 4
        for session in first_plan["sessions"]
    )

    current = client.get(
        "/api/v1/plans/current",
        headers=headers,
    )
    assert current.status_code == 200
    assert current.json()["id"] == first_plan["id"]

    detail = client.get(
        f"/api/v1/plans/{first_plan['id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == first_plan["id"]

    second_plan = generate_plan(client, headers)

    assert second_plan["version"] == 2
    assert second_plan["status"] == "active"
    assert second_plan["start_date"] > first_plan["end_date"]

    plans = client.get(
        "/api/v1/plans",
        headers=headers,
    )
    assert plans.status_code == 200

    history = plans.json()
    assert len(history) == 2
    assert history[0]["status"] == "archived"
    assert history[1]["status"] == "active"


def test_complete_session_and_read_history(
    client: TestClient,
) -> None:
    headers = authenticated_headers(
        client,
        "history@fitplan.dev",
    )
    create_profile(client, headers)

    plan = generate_plan(client, headers)
    session = plan["sessions"][0]
    payload = completion_payload(session)

    completed = client.post(
        f"/api/v1/sessions/{session['id']}/complete",
        headers=headers,
        json=payload,
    )
    assert completed.status_code == 201
    assert completed.json() == {
        "message": "Entrenamiento registrado"
    }

    current = client.get(
        "/api/v1/plans/current",
        headers=headers,
    )
    assert current.status_code == 200
    assert current.json()["sessions"][0]["completed"] is True

    history = client.get(
        "/api/v1/history",
        headers=headers,
    )
    assert history.status_code == 200
    assert len(history.json()) == 1

    record = history.json()[0]
    assert record["session_name"] == session["name"]
    assert record["plan_name"] == plan["name"]
    assert record["difficulty"] == 6
    assert record["energy_level"] == 8
    assert len(record["exercises"]) == len(session["exercises"])

    week_history = client.get(
        "/api/v1/history?period=week",
        headers=headers,
    )
    assert week_history.status_code == 200
    assert len(week_history.json()) == 1

    month_history = client.get(
        "/api/v1/history?period=month",
        headers=headers,
    )
    assert month_history.status_code == 200
    assert len(month_history.json()) == 1

    duplicate = client.post(
        f"/api/v1/sessions/{session['id']}/complete",
        headers=headers,
        json=payload,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == (
        "Esta sesión ya fue completada"
    )


def test_invalid_session_data_is_rejected(
    client: TestClient,
) -> None:
    headers = authenticated_headers(
        client,
        "invalid-session@fitplan.dev",
    )
    create_profile(client, headers)

    plan = generate_plan(client, headers)
    session = plan["sessions"][0]
    payload = completion_payload(session)

    payload["exercises"][0]["actual_weight_kg"] = -1

    negative_weight = client.post(
        f"/api/v1/sessions/{session['id']}/complete",
        headers=headers,
        json=payload,
    )
    assert negative_weight.status_code == 422

    incomplete_payload = completion_payload(session)
    incomplete_payload["exercises"] = (
        incomplete_payload["exercises"][:1]
    )

    incomplete = client.post(
        f"/api/v1/sessions/{session['id']}/complete",
        headers=headers,
        json=incomplete_payload,
    )
    assert incomplete.status_code == 400
    assert incomplete.json()["detail"] == (
        "Debes registrar todos los ejercicios de la sesión"
    )

    invalid_metrics = completion_payload(session)
    invalid_metrics["difficulty"] = 11

    invalid_difficulty = client.post(
        f"/api/v1/sessions/{session['id']}/complete",
        headers=headers,
        json=invalid_metrics,
    )
    assert invalid_difficulty.status_code == 422

    invalid_period = client.get(
        "/api/v1/history?period=year",
        headers=headers,
    )
    assert invalid_period.status_code == 422


def test_successful_performance_increases_recommended_load(
    client: TestClient,
) -> None:
    headers = authenticated_headers(
        client,
        "progression@fitplan.dev",
    )
    create_profile(client, headers)

    first_plan = generate_plan(client, headers)
    session, exercise = find_external_exercise(first_plan)

    previous_weight = exercise["recommended_weight_kg"]

    completed = client.post(
        f"/api/v1/sessions/{session['id']}/complete",
        headers=headers,
        json=completion_payload(
            session,
            difficulty=5,
            energy_level=8,
        ),
    )
    assert completed.status_code == 201

    second_plan = generate_plan(client, headers)
    progressed = find_exercise(
        second_plan,
        exercise["exercise"]["id"],
    )

    assert progressed is not None
    assert (
        progressed["recommended_weight_kg"]
        > previous_weight
    )
    assert second_plan["generation_reason"] == (
        "adapted: progresión por buen rendimiento"
    )


def test_pain_reduces_next_recommended_load(
    client: TestClient,
) -> None:
    headers = authenticated_headers(
        client,
        "pain-adaptation@fitplan.dev",
    )
    create_profile(client, headers)

    first_plan = generate_plan(client, headers)
    session, exercise = find_external_exercise(first_plan)

    previous_weight = exercise["recommended_weight_kg"]

    completed = client.post(
        f"/api/v1/sessions/{session['id']}/complete",
        headers=headers,
        json=completion_payload(
            session,
            difficulty=9,
            energy_level=4,
            pain_reported=True,
        ),
    )
    assert completed.status_code == 201

    second_plan = generate_plan(client, headers)
    adapted = find_exercise(
        second_plan,
        exercise["exercise"]["id"],
    )

    assert adapted is not None
    assert (
        adapted["recommended_weight_kg"]
        < previous_weight
    )
    assert second_plan["generation_reason"] == (
        "adapted: menor volumen por dificultad o molestia"
    )
