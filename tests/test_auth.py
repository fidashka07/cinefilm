from src.models import User


def test_registration(client):
    response = client.post(
        "/auth/register",
        data={
            "username": "cinema_fan",
            "email": "fan@example.com",
            "password": "StrongPassword123",
            "confirm_password": "StrongPassword123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    user = User.query.filter_by(username="cinema_fan").first()

    assert user is not None
    assert user.email == "fan@example.com"
    assert user.check_password("StrongPassword123")


def test_duplicate_registration(client):
    client.post(
        "/auth/register",
        data={
            "username": "cinema_fan",
            "email": "fan@example.com",
            "password": "StrongPassword123",
            "confirm_password": "StrongPassword123",
        },
    )

    response = client.post(
        "/auth/register",
        data={
            "username": "cinema_fan",
            "email": "another@example.com",
            "password": "StrongPassword123",
            "confirm_password": "StrongPassword123",
        },
    )

    assert response.status_code == 200
    assert b"username is already taken" in response.data


def test_login_and_logout(client):
    client.post(
        "/auth/register",
        data={
            "username": "cinema_fan",
            "email": "fan@example.com",
            "password": "StrongPassword123",
            "confirm_password": "StrongPassword123",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "email": "fan@example.com",
            "password": "StrongPassword123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    response = client.post("/auth/logout", follow_redirects=True)

    assert response.status_code == 200


def test_invalid_login(client):
    response = client.post(
        "/auth/login",
        data={
            "email": "unknown@example.com",
            "password": "WrongPassword123",
        },
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data