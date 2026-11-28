from unittest.mock import Mock

import pytest

from src.extensions import db
from src.models import Genre, Movie, Rating, User, WatchlistEntry
from src.services.movie_service import MovieService


class FakeTMDBClient:
    def get_movies(self, category, page):
        return {
            "page": page,
            "total_pages": 5,
            "total_results": 2,
            "results": [
                {
                    "id": 550,
                    "title": "Fight Club",
                    "release_date": "1999-10-15",
                    "genre_ids": [18],
                    "popularity": 100,
                },
                {
                    "id": 551,
                    "title": "Another Movie",
                    "release_date": "2000-01-01",
                    "genre_ids": [18],
                    "popularity": 80,
                },
            ],
        }

    def get_movie_genres(self):
        return [
            {"id": 18, "name": "Drama"},
        ]


def test_get_movies_returns_movies_and_pagination(app):
    with app.app_context():
        service = MovieService(FakeTMDBClient())

        result = service.get_movies("popular", page=2)

        assert len(result["movies"]) == 2
        assert result["page"] == 2
        assert result["total_pages"] == 5
        assert result["total_results"] == 2

        assert result["movies"][0].title == "Fight Club"
        assert result["movies"][1].title == "Another Movie"


def test_get_movies_saves_movies_to_database(app):
    with app.app_context():
        service = MovieService(FakeTMDBClient())

        service.get_movies("popular")

        saved_movies = db.session.execute(
            db.select(Movie)
        ).scalars().all()

        assert len(saved_movies) == 2
        assert Movie.query.filter_by(tmdb_id=550).first() is not None


def test_get_movies_creates_genres(app):
    with app.app_context():
        service = MovieService(FakeTMDBClient())

        service.get_movies("popular")

        genre = Genre.query.filter_by(tmdb_id=18).first()

        assert genre is not None
        assert genre.name == "Drama"


def test_get_movies_rejects_invalid_page(app):
    with app.app_context():
        client = Mock()
        service = MovieService(client)

        with pytest.raises(
            ValueError,
            match="Page must be greater than zero.",
        ):
            service.get_movies("popular", page=0)

        client.get_movies.assert_not_called()


def test_get_movies_rolls_back_when_genre_retrieval_fails(
    app,
    monkeypatch,
):
    with app.app_context():
        client = Mock()
        client.get_movies.return_value = {"results": []}
        client.get_movie_genres.side_effect = RuntimeError(
            "TMDB unavailable"
        )

        rollback = Mock()
        monkeypatch.setattr(
            "src.services.movie_service.MovieRepository.rollback",
            rollback,
        )

        service = MovieService(client)

        with pytest.raises(RuntimeError, match="TMDB unavailable"):
            service.get_movies("popular")

        rollback.assert_called_once()


def test_get_movies_rolls_back_when_saving_fails(
    app,
    monkeypatch,
):
    with app.app_context():
        client = FakeTMDBClient()

        rollback = Mock()
        monkeypatch.setattr(
            "src.services.movie_service.MovieRepository.rollback",
            rollback,
        )

        monkeypatch.setattr(
            "src.services.movie_service.MovieRepository.save_movie",
            Mock(side_effect=RuntimeError("Database error")),
        )

        service = MovieService(client)

        with pytest.raises(RuntimeError, match="Database error"):
            service.get_movies("popular")

        rollback.assert_called_once()


def test_get_movies_handles_empty_results(app):
    with app.app_context():
        client = Mock()
        client.get_movies.return_value = {
            "page": 1,
            "total_pages": 1,
            "total_results": 0,
            "results": [],
        }
        client.get_movie_genres.return_value = []

        service = MovieService(client)

        result = service.get_movies("popular")

        assert result["movies"] == []
        assert result["total_results"] == 0
class FakeRecommendationTMDB:
    def __init__(self):
        self.params = None

    def get_movie_genres(self):
        return [
            {"id": 18, "name": "Drama"},
            {"id": 35, "name": "Comedy"},
            {"id": 28, "name": "Action"},
        ]

    def discover_movies(self, params):
        self.params = params

        return {
            "page": params["page"],
            "total_pages": 3,
            "total_results": 4,
            "results": [
                {"id": 100, "title": "Already Rated"},
                {"id": 200, "title": "Already Watchlisted"},
                {"id": 300, "title": "Recommended One"},
                {"id": 400, "title": "Recommended Two"},
            ],
        }
        
    def search_movies(self, query):
        return {
            "results": [
                {"id": 999, "title": query}
            ]
        }

    def get_movie_recommendations(self, tmdb_id, page=1):
        return {
            "page": page,
            "results": [
                {"id": 500, "title": "Top Movie Recommendation"},
                {"id": 300, "title": "Recommended One"},
            ],
        }


def create_recommendation_user():
    user = User(
        username="recommendation_user",
        email="recommendations@example.com",
        password_hash="test-password",
        favorite_genres=["Comedy"],
    )

    rated_movie = Movie(
        tmdb_id=100,
        title="Already Rated",
        original_title="Already Rated",
    )

    rated_movie.genres.append(
        Genre(tmdb_id=18, name="Drama")
    )

    watchlist_movie = Movie(
        tmdb_id=200,
        title="Already Watchlisted",
        original_title="Already Watchlisted",
    )

    db.session.add_all([
        user,
        rated_movie,
        watchlist_movie,
    ])
    db.session.flush()

    db.session.add_all([
        Rating(
            user_id=user.id,
            movie_id=rated_movie.id,
            score=9.0,
        ),
        WatchlistEntry(
            user_id=user.id,
            movie_id=watchlist_movie.id,
        ),
    ])

    db.session.commit()

    return user


def test_get_movies_for_user_uses_favorite_and_highly_rated_genres(app):
    with app.app_context():
        user = create_recommendation_user()
        client = FakeRecommendationTMDB()
        service = MovieService(client)

        result = service.get_movies_for_user(user)

        assert client.params["with_genres"] == "35|18"
        assert client.params["sort_by"] == "popularity.desc"
        assert client.params["include_adult"] is False
        assert client.params["vote_count.gte"] == 50

        assert result["page"] == 1
        assert result["total_pages"] == 3


def test_get_movies_for_user_excludes_rated_and_watchlisted_movies(app):
    with app.app_context():
        user = create_recommendation_user()
        service = MovieService(FakeRecommendationTMDB())

        result = service.get_movies_for_user(user)

        recommended_ids = [
            movie["id"]
            for movie in result["results"]
        ]

        assert recommended_ids == [300, 400]


def test_get_movies_for_user_uses_popular_fallback_without_preferences(app):
    with app.app_context():
        user = User(
            username="new_user",
            email="newuser@example.com",
            password_hash="test-password",
        )

        db.session.add(user)
        db.session.commit()

        client = FakeRecommendationTMDB()
        service = MovieService(client)

        service.get_movies_for_user(user)

        assert "with_genres" not in client.params
        assert client.params["sort_by"] == "popularity.desc"


def test_get_movies_for_user_supports_pagination(app):
    with app.app_context():
        user = User(
            username="pagination_user",
            email="pagination@example.com",
            password_hash="test-password",
        )

        db.session.add(user)
        db.session.commit()

        client = FakeRecommendationTMDB()
        service = MovieService(client)

        result = service.get_movies_for_user(user, page=2)

        assert client.params["page"] == 2
        assert result["page"] == 2


def test_get_movies_for_user_rejects_invalid_page(app):
    with app.app_context():
        client = FakeRecommendationTMDB()
        service = MovieService(client)

        user = User(
            username="invalid_page_user",
            email="invalidpage@example.com",
            password_hash="test-password",
        )

        with pytest.raises(
            ValueError,
            match="Page must be greater than zero.",
        ):
            service.get_movies_for_user(user, page=0)

        assert client.params is None
def test_get_movie_details_saves_movie_and_returns_details(app):
    with app.app_context():
        client = Mock()
        client.get_movie_details.return_value = {
            "id": 550,
            "title": "Fight Club",
            "original_title": "Fight Club",
            "overview": "An ordinary man...",
            "release_date": "1999-10-15",
            "runtime": 139,
            "genres": [{"id": 18, "name": "Drama"}],
            "credits": {"cast": [], "crew": []},
            "videos": {"results": []},
            "recommendations": {"results": []},
        }

        service = MovieService(client)
        result = service.get_movie_details(550)

        assert result["movie"].title == "Fight Club"
        assert result["movie"].tmdb_id == 550
        assert result["movie"].runtime == 139
        assert [genre.name for genre in result["movie"].genres] == [
            "Drama"
        ]
        assert result["credits"] == {"cast": [], "crew": []}

        assert Movie.query.filter_by(tmdb_id=550).first() is not None


def test_get_movie_details_updates_existing_movie(app):
    with app.app_context():
        client = Mock()
        client.get_movie_details.return_value = {
            "id": 550,
            "title": "Fight Club Updated",
            "genres": [],
            "credits": {},
            "videos": {},
            "recommendations": {},
        }

        service = MovieService(client)
        service.get_movie_details(550)

        client.get_movie_details.return_value["overview"] = "Updated overview"

        result = service.get_movie_details(550)

        assert result["movie"].title == "Fight Club Updated"
        assert result["movie"].overview == "Updated overview"

        assert Movie.query.filter_by(tmdb_id=550).count() == 1

def test_get_movies_for_user_includes_top_movie_recommendations(app):
    with app.app_context():
        user = create_recommendation_user()
        user.top_movies = ["Inception"]
        db.session.commit()

        client = FakeRecommendationTMDB()
        service = MovieService(client)

        result = service.get_movies_for_user(user)

        recommended_ids = [
            movie["id"]
            for movie in result["results"]
        ]

        assert recommended_ids == [500, 300, 400]
        
def test_get_movies_for_user_does_not_infer_genres_from_top_movies(app):
    with app.app_context():
        user = create_recommendation_user()
        user.top_movies = ["Attack on Titan"]
        db.session.commit()

        client = FakeRecommendationTMDB()
        service = MovieService(client)

        service.get_movies_for_user(user)

        # Top 5 movies must not automatically become genre preferences.
        assert client.params["with_genres"] == "35|18"
        assert "16" not in client.params["with_genres"].split("|")