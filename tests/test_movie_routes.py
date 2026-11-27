from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.extensions import db
from src.models import Genre, Movie, Notification, Rating, User, WatchlistEntry
from src.services.tmdb_client import TMDBError
from datetime import date, timedelta
import unittest.mock


@pytest.fixture
def sample_movie(app):
    with app.app_context():
        genre = Genre(tmdb_id=18, name="Drama")

        movie = Movie(
            tmdb_id=550,
            title="Fight Club",
            original_title="Fight Club",
            overview="A movie about identity.",
            release_date=date(1999, 10, 15),
            runtime=139,
            poster_path="/poster.jpg",
            backdrop_path="/backdrop.jpg",
            original_language="en",
            vote_average=8.4,
            vote_count=25000,
            popularity=100,
        )

        movie.genres.append(genre)

        db.session.add(movie)
        db.session.commit()

        return movie.id


def test_get_movies_success(client, app, sample_movie, monkeypatch):
    with app.app_context():
        movie = db.session.get(Movie, sample_movie)

        service = Mock()
        service.get_movies.return_value = {
            "page": 1,
            "total_pages": 5,
            "total_results": 1,
            "movies": [movie],
        }

        monkeypatch.setattr(
            "src.routes.movies.get_movie_service",
            lambda: service,
        )

        response = client.get("/movies/popular")

        assert response.status_code == 200

        data = response.get_json()

        assert data["page"] == 1
        assert data["total_pages"] == 5
        assert data["total_results"] == 1
        assert data["movies"][0]["title"] == "Fight Club"
        assert data["movies"][0]["genres"] == ["Drama"]
        assert data["movies"][0]["release_date"] == "1999-10-15"


def test_get_movies_supports_pagination(client, monkeypatch):
    service = Mock()
    service.get_movies.return_value = {
        "page": 3,
        "total_pages": 5,
        "total_results": 100,
        "movies": [],
    }

    monkeypatch.setattr(
        "src.routes.movies.get_movie_service",
        lambda: service,
    )

    response = client.get("/movies/popular?page=3")

    assert response.status_code == 200
    assert response.get_json()["page"] == 3

    service.get_movies.assert_called_once_with("popular", 3)


def test_get_movies_rejects_invalid_category(client):
    response = client.get("/movies/invalid")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Invalid movie category."


def test_get_movies_rejects_invalid_page(client):
    response = client.get("/movies/popular?page=0")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid page number."


def test_get_movies_handles_tmdb_error(client, monkeypatch):
    service = Mock()
    service.get_movies.side_effect = TMDBError("API unavailable")

    monkeypatch.setattr(
        "src.routes.movies.get_movie_service",
        lambda: service,
    )

    response = client.get("/movies/popular")

    assert response.status_code == 502
    assert "temporarily unavailable" in response.get_json()["error"]


def test_get_movie_details_success(client, app, sample_movie, monkeypatch):
    with app.app_context():
        movie = db.session.get(Movie, sample_movie)

        credits = {
            "crew": [
                {"name": "David Fincher", "job": "Director"},
                {"name": "Someone Else", "job": "Writer"},
            ],
            "cast": [
                {
                    "name": "Actor One",
                    "character": "Character One",
                    "profile_path": "/actor.jpg",
                }
            ],
        }

        videos = {
            "results": [
                {
                    "name": "Official Trailer",
                    "key": "abc123",
                    "site": "YouTube",
                    "type": "Trailer",
                },
                {
                    "name": "Behind the Scenes",
                    "key": "def456",
                    "site": "YouTube",
                    "type": "Behind the Scenes",
                },
                {
                    "name": "Another Trailer",
                    "key": "ghi789",
                    "site": "Vimeo",
                    "type": "Trailer",
                },
            ]
        }

        recommendations = {
            "results": [
                {
                    "id": 551,
                    "title": "Recommended Movie",
                    "poster_path": "/recommended.jpg",
                    "vote_average": 8.0,
                    "release_date": "2000-01-01",
                }
            ]
        }

        service = Mock()
        service.get_movie_details.return_value = {
            "movie": movie,
            "credits": credits,
            "videos": videos,
            "recommendations": recommendations,
        }

        monkeypatch.setattr(
            "src.routes.movies.get_movie_service",
            lambda: service,
        )

        response = client.get("/movies/details/550")

        assert response.status_code == 200

        data = response.get_json()

        assert data["movie"]["title"] == "Fight Club"
        assert data["movie"]["runtime"] == 139
        assert data["movie"]["genres"] == ["Drama"]

        assert data["directors"] == ["David Fincher"]
        assert len(data["cast"]) == 1
        assert data["cast"][0]["name"] == "Actor One"

        assert len(data["trailers"]) == 1
        assert data["trailers"][0]["key"] == "abc123"

        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["title"] == "Recommended Movie"


def test_get_movie_details_limits_cast_and_recommendations(
    client,
    app,
    sample_movie,
    monkeypatch,
):
    with app.app_context():
        movie = db.session.get(Movie, sample_movie)

        cast = [
            {
                "name": f"Actor {i}",
                "character": f"Character {i}",
            }
            for i in range(15)
        ]

        recommendations = [
            {
                "id": i,
                "title": f"Movie {i}",
            }
            for i in range(15)
        ]

        service = Mock()
        service.get_movie_details.return_value = {
            "movie": movie,
            "credits": {"crew": [], "cast": cast},
            "videos": {"results": []},
            "recommendations": {"results": recommendations},
        }

        monkeypatch.setattr(
            "src.routes.movies.get_movie_service",
            lambda: service,
        )

        response = client.get("/movies/details/550")

        data = response.get_json()

        assert len(data["cast"]) == 12
        assert len(data["recommendations"]) == 12


def test_get_movie_details_handles_tmdb_error(client, monkeypatch):
    service = Mock()
    service.get_movie_details.side_effect = TMDBError(
        "API unavailable"
    )

    monkeypatch.setattr(
        "src.routes.movies.get_movie_service",
        lambda: service,
    )

    response = client.get("/movies/details/550")

    assert response.status_code == 502
    assert "temporarily unavailable" in response.get_json()["error"]

def create_watchlist_test_user():
    user = User(
        username="watchlisttester",
        email="watchlisttester@example.com",
    )
    user.set_password("Password123")
    db.session.add(user)
    db.session.commit()
    return user


def login_test_user(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True


def test_adding_upcoming_movie_creates_immediate_notification(
    client, app, monkeypatch
):
    with app.app_context():
        user = create_watchlist_test_user()
        login_test_user(client, user)

        movie = Movie(
            tmdb_id=9001,
            title="Upcoming Movie",
            release_date=date.today() + timedelta(days=5),
        )
        db.session.add(movie)
        db.session.commit()

        monkeypatch.setattr(
            "src.routes.movies.get_movie_service",
            lambda: Mock(),
        )

        response = client.post("/movies/watchlist/9001")

        assert response.status_code == 201

        notification = Notification.query.one()
        assert notification.user_id == user.id
        assert notification.movie_id == movie.id
        assert notification.notification_type == "added_to_watchlist"


@pytest.mark.parametrize(
    "release_date",
    [
        date.today() - timedelta(days=1),
        None,
    ],
)
def test_adding_released_or_unknown_date_movie_creates_no_notification(
    client, app, monkeypatch, release_date
):
    with app.app_context():
        user = create_watchlist_test_user()
        login_test_user(client, user)

        movie = Movie(
            tmdb_id=9002,
            title="Existing Movie",
            release_date=release_date,
        )
        db.session.add(movie)
        db.session.commit()

        monkeypatch.setattr(
            "src.routes.movies.get_movie_service",
            lambda: Mock(),
        )

        response = client.post("/movies/watchlist/9002")

        assert response.status_code == 201
        assert Notification.query.count() == 0
        assert WatchlistEntry.query.count() == 1


def test_adding_same_movie_twice_does_not_create_duplicate_notification(
    client, app, monkeypatch
):
    with app.app_context():
        user = create_watchlist_test_user()
        login_test_user(client, user)

        movie = Movie(
            tmdb_id=9003,
            title="Duplicate Movie",
            release_date=date.today() + timedelta(days=5),
        )
        db.session.add(movie)
        db.session.commit()

        monkeypatch.setattr(
            "src.routes.movies.get_movie_service",
            lambda: Mock(),
        )

        first_response = client.post("/movies/watchlist/9003")
        second_response = client.post("/movies/watchlist/9003")

        assert first_response.status_code == 201
        assert second_response.status_code == 409
        assert Notification.query.count() == 1
        assert WatchlistEntry.query.count() == 1
        
def login_for_you_test_user(client, app):
    with app.app_context():
        user = User(
            username="for_you_user",
            email="foryou@example.com",
        )
        user.set_password("StrongPassword123")

        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True

    return user_id

def test_for_you_requires_authentication(client):
    response = client.get("/movies/for-you")

    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_for_you_returns_recommendations(client, app, monkeypatch):
    login_for_you_test_user(client, app)

    service = Mock()
    service.get_movies_for_user.return_value = {
        "page": 1,
        "total_pages": 3,
        "total_results": 2,
        "results": [
            {
                "id": 550,
                "title": "Fight Club",
                "overview": "A movie about identity.",
                "release_date": "1999-10-15",
                "poster_path": "/poster.jpg",
                "backdrop_path": "/backdrop.jpg",
                "vote_average": 8.4,
                "genre_ids": [18],
            }
        ],
    }

    monkeypatch.setattr(
        "src.routes.movies.get_movie_service",
        lambda: service,
    )

    response = client.get("/movies/for-you")

    assert response.status_code == 200

    data = response.get_json()

    assert data["page"] == 1
    assert data["total_pages"] == 3
    assert data["total_results"] == 2
    assert data["movies"][0]["tmdb_id"] == 550
    assert data["movies"][0]["title"] == "Fight Club"

    service.get_movies_for_user.assert_called_once()


def test_for_you_supports_pagination(client, app, monkeypatch):
    login_for_you_test_user(client, app)
    service = Mock()
    service.get_movies_for_user.return_value = {
        "page": 2,
        "total_pages": 3,
        "total_results": 20,
        "results": [],
    }

    monkeypatch.setattr(
        "src.routes.movies.get_movie_service",
        lambda: service,
    )

    response = client.get("/movies/for-you?page=2")

    assert response.status_code == 200
    assert response.get_json()["page"] == 2

    service.get_movies_for_user.assert_called_once_with(
        unittest.mock.ANY,
        2,
    )


def test_for_you_rejects_invalid_page(client, app):
    login_for_you_test_user(client, app)

    response = client.get("/movies/for-you?page=0")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid page number."


def test_for_you_handles_tmdb_error(client, app, monkeypatch):
    login_for_you_test_user(client, app)
    service = Mock()
    service.get_movies_for_user.side_effect = TMDBError(
        "API unavailable"
    )

    monkeypatch.setattr(
        "src.routes.movies.get_movie_service",
        lambda: service,
    )

    response = client.get("/movies/for-you")

    assert response.status_code == 502
    assert "temporarily unavailable" in response.get_json()["error"]

def test_rating_endpoint_creates_new_rating(
    client, app, sample_movie
):
    with app.app_context():
        user = create_watchlist_test_user()
        login_test_user(client, user)

        movie = db.session.get(Movie, sample_movie)

        response = client.post(
            f"/movies/{movie.tmdb_id}/rating",
            json={"score": 9.5},
        )

        assert response.status_code == 200
        assert response.get_json()["score"] == 9.5

        rating = Rating.query.filter_by(
            user_id=user.id,
            movie_id=movie.id,
        ).one()

        assert rating.score == 9.5


def test_rating_endpoint_updates_existing_rating(
    client, app, sample_movie
):
    with app.app_context():
        user = create_watchlist_test_user()
        login_test_user(client, user)

        movie = db.session.get(Movie, sample_movie)

        rating = Rating(
            user_id=user.id,
            movie_id=movie.id,
            score=7.0,
        )
        db.session.add(rating)
        db.session.commit()

        response = client.post(
            f"/movies/{movie.tmdb_id}/rating",
            json={"score": 9.5},
        )

        assert response.status_code == 200
        assert response.get_json()["score"] == 9.5
        assert Rating.query.count() == 1
        assert rating.score == 9.5


@pytest.mark.parametrize(
    "score",
    [0, 10.5, 11, 4.25, "9", None, True],
)
def test_rating_endpoint_rejects_invalid_scores(
    client, app, sample_movie, score
):
    with app.app_context():
        user = create_watchlist_test_user()
        login_test_user(client, user)

        movie = db.session.get(Movie, sample_movie)

        response = client.post(
            f"/movies/{movie.tmdb_id}/rating",
            json={"score": score},
        )

        assert response.status_code == 400
        assert "error" in response.get_json()


def test_rating_endpoint_requires_login(client, sample_movie):
    response = client.post(
        "/movies/550/rating",
        json={"score": 9.0},
    )

    assert response.status_code == 302


def test_rating_endpoint_returns_404_for_missing_movie(
    client, app
):
    with app.app_context():
        user = create_watchlist_test_user()
        login_test_user(client, user)

        response = client.post(
            "/movies/999999/rating",
            json={"score": 9.0},
        )

        assert response.status_code == 404
        assert response.get_json()["error"] == "Movie not found."
