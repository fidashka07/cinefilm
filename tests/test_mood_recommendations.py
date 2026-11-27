from unittest.mock import Mock


def test_mood_recommendations_success(client, monkeypatch):
    service = Mock()

    service.get_movies_by_mood.return_value = {
        "page": 1,
        "total_pages": 3,
        "total_results": 50,
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

    response = client.get("/movies/mood/mind-blown")

    assert response.status_code == 200

    data = response.get_json()

    assert data["page"] == 1
    assert data["total_pages"] == 3
    assert data["movies"][0]["tmdb_id"] == 550
    assert data["movies"][0]["title"] == "Fight Club"

    service.get_movies_by_mood.assert_called_once_with(
        "mind-blown",
        1,
    )


def test_mood_recommendations_reject_invalid_mood(client):
    response = client.get("/movies/mood/invalid")

    assert response.status_code == 404


def test_mood_recommendations_reject_invalid_page(client):
    response = client.get("/movies/mood/happy?page=0")

    assert response.status_code == 400


def test_mood_recommendations_support_pagination(client, monkeypatch):
    service = Mock()

    service.get_movies_by_mood.return_value = {
        "page": 2,
        "total_pages": 5,
        "total_results": 100,
        "results": [],
    }

    monkeypatch.setattr(
        "src.routes.movies.get_movie_service",
        lambda: service,
    )

    response = client.get("/movies/mood/romantic?page=2")

    assert response.status_code == 200
    assert response.get_json()["page"] == 2

    service.get_movies_by_mood.assert_called_once_with(
        "romantic",
        2,
    )


def test_mood_recommendations_handle_tmdb_error(client, monkeypatch):
    from src.services.tmdb_client import TMDBError

    service = Mock()

    service.get_movies_by_mood.side_effect = TMDBError(
        "API unavailable"
    )

    monkeypatch.setattr(
        "src.routes.movies.get_movie_service",
        lambda: service,
    )

    response = client.get("/movies/mood/happy")

    assert response.status_code == 502