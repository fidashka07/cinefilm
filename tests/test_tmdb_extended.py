import time
from unittest.mock import Mock

import pytest
import requests

from src.services.tmdb_client import TMDBClient, TMDBError


@pytest.fixture
def client():
    return TMDBClient(
        token="test-token",
        base_url="https://api.themoviedb.org/3/",
        timeout=5,
    )


def test_client_removes_trailing_slash(client):
    assert client.base_url == "https://api.themoviedb.org/3"


def test_client_configures_authentication_headers(client):
    assert client.session.headers["Authorization"] == "Bearer test-token"
    assert client.session.headers["accept"] == "application/json"


def test_client_uses_custom_timeout(client):
    assert client.timeout == 5


def test_get_returns_api_response(client, monkeypatch):
    response = Mock()
    response.json.return_value = {"title": "Fight Club"}

    request = Mock(return_value=response)
    monkeypatch.setattr(client.session, "get", request)

    result = client.get("movie/550")

    assert result == {"title": "Fight Club"}

    request.assert_called_once_with(
        "https://api.themoviedb.org/3/movie/550",
        params={},
        timeout=5,
    )


def test_get_uses_cache(client, monkeypatch):
    response = Mock()
    response.json.return_value = {"title": "Fight Club"}

    request = Mock(return_value=response)
    monkeypatch.setattr(client.session, "get", request)

    first = client.get("movie/550")
    second = client.get("movie/550")

    assert first == second
    assert request.call_count == 1


def test_get_cache_distinguishes_parameters(client, monkeypatch):
    response = Mock()
    response.json.side_effect = [
        {"page": 1},
        {"page": 2},
    ]

    request = Mock(return_value=response)
    monkeypatch.setattr(client.session, "get", request)

    first = client.get("movie/popular", {"page": 1})
    second = client.get("movie/popular", {"page": 2})

    assert first["page"] == 1
    assert second["page"] == 2
    assert request.call_count == 2


def test_get_refreshes_expired_cache(client, monkeypatch):
    response = Mock()
    response.json.side_effect = [
        {"title": "Old"},
        {"title": "New"},
    ]

    request = Mock(return_value=response)
    monkeypatch.setattr(client.session, "get", request)

    first = client.get("movie/550", cache_seconds=0)
    second = client.get("movie/550", cache_seconds=0)

    assert first["title"] == "Old"
    assert second["title"] == "New"
    assert request.call_count == 2


def test_get_handles_request_exception(client, monkeypatch):
    monkeypatch.setattr(
        client.session,
        "get",
        Mock(side_effect=requests.ConnectionError("Network error")),
    )

    with pytest.raises(TMDBError, match="Unable to communicate"):
        client.get("movie/550")


def test_get_handles_invalid_json(client, monkeypatch):
    response = Mock()
    response.json.side_effect = ValueError("Invalid JSON")

    monkeypatch.setattr(
        client.session,
        "get",
        Mock(return_value=response),
    )

    with pytest.raises(TMDBError, match="invalid JSON"):
        client.get("movie/550")


def test_get_movie_genres(client, monkeypatch):
    monkeypatch.setattr(
        client,
        "get",
        Mock(return_value={
            "genres": [{"id": 18, "name": "Drama"}]
        }),
    )

    result = client.get_movie_genres()

    assert result == [{"id": 18, "name": "Drama"}]


def test_get_movie_genres_returns_empty_list(client, monkeypatch):
    monkeypatch.setattr(
        client,
        "get",
        Mock(return_value={}),
    )

    assert client.get_movie_genres() == []


def test_get_movie_details(client, monkeypatch):
    request = Mock(return_value={"id": 550})
    monkeypatch.setattr(client, "get", request)

    result = client.get_movie_details(550)

    assert result == {"id": 550}

    request.assert_called_once_with(
        "movie/550",
        params={
            "append_to_response": "credits,videos,recommendations"
        },
    )


@pytest.mark.parametrize(
    ("category", "expected_endpoint"),
    [
        ("trending", "trending/movie/week"),
        ("popular", "movie/popular"),
        ("top-rated", "movie/top_rated"),
        ("upcoming", "movie/upcoming"),
    ],
)
def test_get_movies_uses_correct_endpoint(
    client,
    monkeypatch,
    category,
    expected_endpoint,
):
    request = Mock(return_value={"results": []})
    monkeypatch.setattr(client, "get", request)

    result = client.get_movies(category, page=2)

    assert result == {"results": []}

    request.assert_called_once_with(
        expected_endpoint,
        params={"page": 2},
    )


def test_get_movies_rejects_invalid_category(client):
    with pytest.raises(ValueError, match="Invalid movie category"):
        client.get_movies("unknown")