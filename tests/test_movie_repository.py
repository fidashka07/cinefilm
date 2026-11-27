from datetime import date
import pytest
from src.extensions import db
from src.models import Genre, Movie
from src.repositories.movie_repository import MovieRepository


@pytest.fixture
def genre_map(app):
    with app.app_context():
        action = Genre(tmdb_id=28, name="Action")
        drama = Genre(tmdb_id=18, name="Drama")

        db.session.add_all([action, drama])
        db.session.commit()

        return {
            28: action,
            18: drama,
        }


@pytest.fixture
def sample_movies(app):
    with app.app_context():
        movies = [
            Movie(
                tmdb_id=101,
                title="Movie A",
                popularity=50,
                vote_average=7.5,
            ),
            Movie(
                tmdb_id=102,
                title="Movie B",
                popularity=90,
                vote_average=8.5,
            ),
            Movie(
                tmdb_id=103,
                title="Movie C",
                popularity=30,
                vote_average=6.5,
            ),
        ]

        db.session.add_all(movies)
        db.session.commit()

        return movies


def test_get_by_tmdb_id(app, sample_movies):
    with app.app_context():
        movie = MovieRepository.get_by_tmdb_id(102)

        assert movie is not None
        assert movie.title == "Movie B"


def test_get_by_tmdb_id_returns_none_when_not_found(app):
    with app.app_context():
        movie = MovieRepository.get_by_tmdb_id(999)

        assert movie is None


def test_get_all_orders_by_popularity(app, sample_movies):
    with app.app_context():
        movies = MovieRepository.get_all()

        assert [movie.tmdb_id for movie in movies] == [
            102, 101, 103
        ]


def test_get_by_category_order(app, sample_movies):
    with app.app_context():
        movies = MovieRepository.get_by_category_order(
            Movie.vote_average,
            page=1,
            per_page=2,
        )

        assert [movie.tmdb_id for movie in movies] == [
            102, 101
        ]


def test_get_by_category_order_pagination(app, sample_movies):
    with app.app_context():
        movies = MovieRepository.get_by_category_order(
            Movie.popularity,
            page=2,
            per_page=2,
        )

        assert len(movies) == 1
        assert movies[0].tmdb_id == 103


def test_get_or_create_genre_creates_new_genre(app):
    with app.app_context():
        genre = MovieRepository.get_or_create_genre({
            "id": 28,
            "name": "Action",
        })

        assert genre.id is not None
        assert genre.tmdb_id == 28
        assert genre.name == "Action"

        saved_genre = db.session.get(Genre, genre.id)
        assert saved_genre is not None


def test_get_or_create_genre_reuses_existing_genre(app):
    with app.app_context():
        existing = Genre(tmdb_id=28, name="Action")
        db.session.add(existing)
        db.session.commit()

        genre = MovieRepository.get_or_create_genre({
            "id": 28,
            "name": "Action",
        })

        assert genre.id == existing.id

        count = db.session.execute(
            db.select(db.func.count()).select_from(Genre)
        ).scalar_one()

        assert count == 1


def test_save_movie_creates_new_movie(app, genre_map):
    with app.app_context():
        data = {
            "id": 550,
            "title": "Fight Club",
            "original_title": "Fight Club",
            "overview": "A movie overview.",
            "release_date": "1999-10-15",
            "runtime": 139,
            "poster_path": "/poster.jpg",
            "backdrop_path": "/backdrop.jpg",
            "original_language": "en",
            "vote_average": 8.4,
            "vote_count": 25000,
            "popularity": 100.5,
            "genre_ids": [18, 28],
        }

        movie = MovieRepository.save_movie(data, genre_map)
        db.session.commit()

        assert movie.id is not None
        assert movie.tmdb_id == 550
        assert movie.title == "Fight Club"
        assert movie.release_date == date(1999, 10, 15)
        assert movie.runtime == 139
        assert len(movie.genres) == 2


def test_save_movie_updates_existing_movie(app, genre_map):
    with app.app_context():
        existing = Movie(
            tmdb_id=550,
            title="Old Title",
            runtime=120,
        )
        db.session.add(existing)
        db.session.commit()

        data = {
            "id": 550,
            "title": "Fight Club",
            "runtime": 139,
            "release_date": "1999-10-15",
            "genre_ids": [18],
        }

        movie = MovieRepository.save_movie(data, genre_map)
        db.session.commit()

        assert movie.id == existing.id
        assert movie.title == "Fight Club"
        assert movie.runtime == 139
        assert len(movie.genres) == 1


def test_save_movie_handles_missing_release_date(app):
    with app.app_context():
        movie = MovieRepository.save_movie(
            {"id": 600, "title": "Unknown Movie"},
            {},
        )

        assert movie.release_date is None
        assert movie.title == "Unknown Movie"


def test_save_movie_handles_invalid_release_date(app):
    with app.app_context():
        movie = MovieRepository.save_movie(
            {
                "id": 601,
                "title": "Invalid Date Movie",
                "release_date": "not-a-date",
            },
            {},
        )

        assert movie.release_date is None


def test_save_movie_uses_untitled_when_title_missing(app):
    with app.app_context():
        movie = MovieRepository.save_movie(
            {"id": 602},
            {},
        )

        assert movie.title == "Untitled"


def test_save_movie_ignores_unknown_genre_ids(app, genre_map):
    with app.app_context():
        movie = MovieRepository.save_movie(
            {
                "id": 603,
                "title": "Test Movie",
                "genre_ids": [28, 999],
            },
            genre_map,
        )

        assert len(movie.genres) == 1
        assert movie.genres[0].tmdb_id == 28


def test_save_movie_preserves_runtime_when_missing(app):
    with app.app_context():
        existing = Movie(
            tmdb_id=604,
            title="Existing Movie",
            runtime=120,
        )
        db.session.add(existing)
        db.session.commit()

        movie = MovieRepository.save_movie(
            {
                "id": 604,
                "title": "Updated Movie",
            },
            {},
        )

        assert movie.runtime == 120


def test_commit_and_rollback(app):
    with app.app_context():
        movie = Movie(tmdb_id=700, title="Committed Movie")
        db.session.add(movie)

        MovieRepository.commit()

        assert MovieRepository.get_by_tmdb_id(700) is not None

        another_movie = Movie(
            tmdb_id=701,
            title="Rolled Back Movie",
        )
        db.session.add(another_movie)

        MovieRepository.rollback()

        assert MovieRepository.get_by_tmdb_id(701) is None