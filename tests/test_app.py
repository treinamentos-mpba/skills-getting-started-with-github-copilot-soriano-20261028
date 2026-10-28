from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    atividades_originais = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(atividades_originais)


def test_root_redirects_to_static_index(client: TestClient):
    """Arrange: preparar o cliente da API."""
    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_lists_all_activities(client: TestClient):
    """Arrange: preparar o cliente e obter os dados de referência."""
    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signs_up_student_for_activity(client: TestClient):
    """Arrange: selecionar atividade e estudante ainda não inscritos."""
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_sign_up_for_nonexistent_activity_returns_not_found(client: TestClient):
    """Arrange: selecionar uma atividade inexistente."""
    activity_name = "Nonexistent Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signing_up_twice_returns_bad_request(client: TestClient):
    """Arrange: escolher estudante já inscrito na atividade."""
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_sign_up_for_full_activity_returns_bad_request(client: TestClient):
    """Arrange: preencher todas as vagas da atividade."""
    activity_name = "Chess Club"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregisters_student_from_activity(client: TestClient):
    """Arrange: selecionar estudante inscrito na atividade."""
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


def test_unregister_from_nonexistent_activity_returns_not_found(
    client: TestClient,
):
    """Arrange: selecionar uma atividade inexistente."""
    activity_name = "Nonexistent Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregistering_nonparticipant_returns_not_found(client: TestClient):
    """Arrange: escolher estudante não inscrito na atividade."""
    activity_name = "Chess Club"
    email = "not-enrolled@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
