import pytest

from src.services.tmdb_client import TMDBClient, TMDBError


def test_tmdb_client_requires_token():
    with pytest.raises(ValueError):
        TMDBClient(
            token=None,
            base_url="https://api.themoviedb.org/3",
        )


def test_tmdb_client_uses_bearer_authentication():
    client = TMDBClient(
        token="test-token",
        base_url="https://api.themoviedb.org/3",
    )

    assert (
        client.session.headers["Authorization"]
        == "Bearer test-token"
    )


def test_invalid_movie_category():
    client = TMDBClient(
        token="test-token",
        base_url="https://api.themoviedb.org/3",
    )

    with pytest.raises(ValueError):
        client.get_movies("invalid-category")


def test_tmdb_client_handles_http_errors(monkeypatch):
    import requests

    client = TMDBClient(
        token="test-token",
        base_url="https://api.themoviedb.org/3",
    )

    def mock_get(*args, **kwargs):
        response = requests.Response()
        response.status_code = 500
        response.url = "https://api.themoviedb.org/3/movie/popular"
        return response

    monkeypatch.setattr(client.session, "get", mock_get)

    with pytest.raises(TMDBError):
        client.get("movie/popular")