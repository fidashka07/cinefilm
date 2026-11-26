from src.extensions import db
from src.models import Genre, Movie, Rating, User, WatchlistEntry


def test_user_password_hashing(app):
    user = User(
        username="testuser",
        email="test@example.com",
    )

    user.set_password("SecurePassword123")

    assert user.password_hash != "SecurePassword123"
    assert user.check_password("SecurePassword123")
    assert not user.check_password("WrongPassword")


def test_movie_genre_relationship(app):
    movie = Movie(
        tmdb_id=12345,
        title="Inception",
    )

    genre = Genre(
        tmdb_id=28,
        name="Action",
    )

    movie.genres.append(genre)

    db.session.add(movie)
    db.session.commit()

    saved_movie = db.session.get(Movie, movie.id)

    assert len(saved_movie.genres) == 1
    assert saved_movie.genres[0].name == "Action"


def test_user_can_add_movie_to_watchlist(app):
    user = User(
        username="cinemafan",
        email="fan@example.com",
    )
    user.set_password("Password123")

    movie = Movie(
        tmdb_id=67890,
        title="Interstellar",
    )

    db.session.add_all([user, movie])
    db.session.flush()

    entry = WatchlistEntry(
        user_id=user.id,
        movie_id=movie.id,
    )

    db.session.add(entry)
    db.session.commit()

    assert len(user.watchlist_entries) == 1
    assert user.watchlist_entries[0].movie.title == "Interstellar"


def test_user_can_rate_movie(app):
    user = User(
        username="reviewer",
        email="reviewer@example.com",
    )
    user.set_password("Password123")

    movie = Movie(
        tmdb_id=99999,
        title="The Prestige",
    )

    db.session.add_all([user, movie])
    db.session.flush()

    rating = Rating(
        user_id=user.id,
        movie_id=movie.id,
        score=4.5,
    )

    db.session.add(rating)
    db.session.commit()

    assert user.ratings[0].score == 4.5