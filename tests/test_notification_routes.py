from datetime import UTC, date, datetime

from src.extensions import db
from src.models import Movie, Notification, User, WatchlistEntry


def create_user(username):
    user = User(
        username=username,
        email=f"{username}@example.com",
    )
    user.set_password("Password123")
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True


def create_movie(tmdb_id, title):
    movie = Movie(tmdb_id=tmdb_id, title=title)
    db.session.add(movie)
    db.session.commit()
    return movie


def create_notification(user, movie, notification_type="added_to_watchlist"):
    notification = Notification(
        user_id=user.id,
        movie_id=movie.id,
        notification_type=notification_type,
        message=f"{movie.title} notification.",
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def test_notifications_page_requires_login(client):
    response = client.get("/notifications/")

    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_unread_count_requires_login(client):
    response = client.get("/notifications/unread-count")

    assert response.status_code == 302


def test_watchlist_page_requires_login(client):
    response = client.get("/notifications/watchlist")

    assert response.status_code == 302


def test_authenticated_user_can_open_notifications(client, app):
    with app.app_context():
        user = create_user("routeuser1")
        login_as(client, user)

        response = client.get("/notifications/")

        assert response.status_code == 200
        assert b"Notifications" in response.data


def test_unread_count_returns_correct_number(client, app):
    with app.app_context():
        user = create_user("routeuser2")
        movie1 = create_movie(2001, "Movie One")
        movie2 = create_movie(2002, "Movie Two")

        create_notification(user, movie1)
        create_notification(user, movie2)

        login_as(client, user)

        response = client.get("/notifications/unread-count")

        assert response.status_code == 200
        assert response.get_json() == {"count": 2}


def test_user_can_mark_notification_as_read(client, app):
    with app.app_context():
        user = create_user("routeuser3")
        movie = create_movie(2003, "Read Movie")
        notification = create_notification(user, movie)

        login_as(client, user)

        response = client.post(
            f"/notifications/{notification.id}/read"
        )

        assert response.status_code == 200
        assert response.get_json() == {
            "message": "Notification marked as read."
        }

        saved = db.session.get(Notification, notification.id)
        assert saved.read_at is not None


def test_user_cannot_mark_another_users_notification_as_read(
    client,
    app,
):
    with app.app_context():
        owner = create_user("notificationowner")
        another_user = create_user("notificationother")

        movie = create_movie(2004, "Private Movie")
        notification = create_notification(owner, movie)

        login_as(client, another_user)

        response = client.post(
            f"/notifications/{notification.id}/read"
        )

        assert response.status_code == 404

        saved = db.session.get(Notification, notification.id)
        assert saved.read_at is None


def test_mark_all_notifications_as_read(client, app):
    with app.app_context():
        user = create_user("routeuser5")

        movie1 = create_movie(2005, "First Movie")
        movie2 = create_movie(2006, "Second Movie")

        create_notification(user, movie1)
        create_notification(user, movie2)

        login_as(client, user)

        response = client.post("/notifications/read-all")

        assert response.status_code == 200
        assert response.get_json() == {
            "message": "All notifications marked as read."
        }

        assert (
            db.session.query(Notification)
            .filter_by(user_id=user.id, read_at=None)
            .count()
            == 0
        )


def test_user_only_sees_their_own_watchlist(client, app):
    with app.app_context():
        user1 = create_user("watchlistuser1")
        user2 = create_user("watchlistuser2")

        movie1 = create_movie(2007, "User One Movie")
        movie2 = create_movie(2008, "User Two Movie")

        db.session.add_all([
            WatchlistEntry(user_id=user1.id, movie_id=movie1.id),
            WatchlistEntry(user_id=user2.id, movie_id=movie2.id),
        ])
        db.session.commit()

        login_as(client, user1)

        response = client.get("/notifications/watchlist")

        assert response.status_code == 200
        assert b"User One Movie" in response.data
        assert b"User Two Movie" not in response.data


def test_unread_count_does_not_include_other_users_notifications(
    client,
    app,
):
    with app.app_context():
        user1 = create_user("countuser1")
        user2 = create_user("countuser2")

        movie1 = create_movie(2009, "First Private Movie")
        movie2 = create_movie(2010, "Second Private Movie")

        create_notification(user1, movie1)
        create_notification(user2, movie2)

        login_as(client, user1)

        response = client.get("/notifications/unread-count")

        assert response.status_code == 200
        assert response.get_json() == {"count": 1}
