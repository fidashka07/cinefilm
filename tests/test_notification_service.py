from datetime import date, timedelta

from src.extensions import db
from src.models import Movie, Notification, User, WatchlistEntry
from src.services.notification_service import NotificationService


class FakeDate(date):
    @classmethod
    def today(cls):
        return cls(2026, 11, 28)


def create_user(username):
    user = User(
        username=username,
        email=f"{username}@example.com",
    )
    user.set_password("Password123")
    db.session.add(user)
    db.session.flush()
    return user


def create_movie(tmdb_id, title, release_date=None):
    movie = Movie(
        tmdb_id=tmdb_id,
        title=title,
        release_date=release_date,
    )
    db.session.add(movie)
    db.session.flush()
    return movie


def add_to_watchlist(user, movie):
    entry = WatchlistEntry(
        user_id=user.id,
        movie_id=movie.id,
    )
    db.session.add(entry)
    db.session.commit()


def test_generates_seven_day_release_reminder(app, monkeypatch):
    import src.services.notification_service as service_module

    monkeypatch.setattr(service_module, "date", FakeDate)

    user = create_user("fan1")
    movie = create_movie(
        1001,
        "Upcoming Movie",
        date(2026, 12, 5),
    )
    add_to_watchlist(user, movie)

    NotificationService.generate_due(user)

    notification = Notification.query.one()

    assert notification.notification_type == "release_reminder"
    assert notification.message == "Upcoming Movie releases in 7 days."


def test_generates_release_day_notification(app, monkeypatch):
    import src.services.notification_service as service_module

    monkeypatch.setattr(service_module, "date", FakeDate)

    user = create_user("fan2")
    movie = create_movie(
        1002,
        "Released Today",
        date(2026, 11, 28),
    )
    add_to_watchlist(user, movie)

    NotificationService.generate_due(user)

    notification = Notification.query.one()

    assert notification.notification_type == "release_day"
    assert notification.message == (
        "Released Today is out today! It's time to watch."
    )


def test_does_not_notify_for_already_released_movie(app, monkeypatch):
    import src.services.notification_service as service_module

    monkeypatch.setattr(service_module, "date", FakeDate)

    user = create_user("fan3")
    movie = create_movie(
        1003,
        "Old Movie",
        date(2026, 11, 27),
    )
    add_to_watchlist(user, movie)

    NotificationService.generate_due(user)

    assert Notification.query.count() == 0


def test_does_not_notify_when_release_date_is_unknown(app, monkeypatch):
    import src.services.notification_service as service_module

    monkeypatch.setattr(service_module, "date", FakeDate)

    user = create_user("fan4")
    movie = create_movie(1004, "Unknown Release")

    add_to_watchlist(user, movie)

    NotificationService.generate_due(user)

    assert Notification.query.count() == 0


def test_does_not_notify_for_movies_releasing_after_seven_days(
    app,
    monkeypatch,
):
    import src.services.notification_service as service_module

    monkeypatch.setattr(service_module, "date", FakeDate)

    user = create_user("fan5")
    movie = create_movie(
        1005,
        "Far Future Movie",
        date(2026, 12, 6),
    )
    add_to_watchlist(user, movie)

    NotificationService.generate_due(user)

    assert Notification.query.count() == 0


def test_does_not_create_duplicate_notifications(app, monkeypatch):
    import src.services.notification_service as service_module

    monkeypatch.setattr(service_module, "date", FakeDate)

    user = create_user("fan6")
    movie = create_movie(
        1006,
        "Duplicate Test",
        date(2026, 12, 2),
    )
    add_to_watchlist(user, movie)

    NotificationService.generate_due(user)
    NotificationService.generate_due(user)

    assert Notification.query.count() == 1


def test_generates_notifications_only_for_users_own_watchlist(
    app,
    monkeypatch,
):
    import src.services.notification_service as service_module

    monkeypatch.setattr(service_module, "date", FakeDate)

    user1 = create_user("fan7")
    user2 = create_user("fan8")

    movie1 = create_movie(
        1007,
        "User One Movie",
        date(2026, 12, 2),
    )
    movie2 = create_movie(
        1008,
        "User Two Movie",
        date(2026, 12, 3),
    )

    add_to_watchlist(user1, movie1)
    add_to_watchlist(user2, movie2)

    NotificationService.generate_due(user1)

    notifications = Notification.query.all()

    assert len(notifications) == 1
    assert notifications[0].user_id == user1.id
    assert notifications[0].movie_id == movie1.id


def test_unread_count_is_separate_for_each_user(app):
    user1 = create_user("fan9")
    user2 = create_user("fan10")

    movie1 = create_movie(1009, "Movie One")
    movie2 = create_movie(1010, "Movie Two")

    db.session.add_all([
        Notification(
            user_id=user1.id,
            movie_id=movie1.id,
            notification_type="added_to_watchlist",
            message="Movie One added to your watchlist.",
        ),
        Notification(
            user_id=user1.id,
            movie_id=movie2.id,
            notification_type="added_to_watchlist",
            message="Movie Two added to your watchlist.",
        ),
        Notification(
            user_id=user2.id,
            movie_id=movie2.id,
            notification_type="added_to_watchlist",
            message="Movie Two added to your watchlist.",
        ),
    ])
    db.session.commit()

    assert NotificationService.unread_count(user1.id) == 2
    assert NotificationService.unread_count(user2.id) == 1


def test_read_notifications_are_not_counted_as_unread(app):
    user = create_user("fan11")
    movie = create_movie(1011, "Read Test")

    notification = Notification(
        user_id=user.id,
        movie_id=movie.id,
        notification_type="added_to_watchlist",
        message="Added to watchlist.",
        read_at=None,
    )

    db.session.add(notification)
    db.session.commit()

    assert NotificationService.unread_count(user.id) == 1

    notification.read_at = date(2026, 11, 28)
    db.session.commit()

    assert NotificationService.unread_count(user.id) == 0
