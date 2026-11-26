from datetime import date

from src.extensions import db
from src.models import Genre, Movie


class MovieRepository:
    """Handles movie and genre database operations."""

    @staticmethod
    def get_by_tmdb_id(tmdb_id):
        return db.session.execute(
            db.select(Movie).filter_by(tmdb_id=tmdb_id)
        ).scalar_one_or_none()

    @staticmethod
    def get_all():
        return db.session.execute(
            db.select(Movie).order_by(Movie.popularity.desc())
        ).scalars().all()

    @staticmethod
    def get_by_category_order(order_column, page=1, per_page=20):
        statement = (
            db.select(Movie)
            .order_by(order_column.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )

        return db.session.execute(statement).scalars().all()

    @staticmethod
    def get_or_create_genre(tmdb_genre):
        genre = db.session.execute(
            db.select(Genre).filter_by(
                tmdb_id=tmdb_genre["id"]
            )
        ).scalar_one_or_none()

        if genre is None:
            genre = Genre(
                tmdb_id=tmdb_genre["id"],
                name=tmdb_genre["name"],
            )
            db.session.add(genre)
            db.session.flush()

        return genre

    @staticmethod
    def save_movie(data, genre_map):
        movie = MovieRepository.get_by_tmdb_id(data["id"])

        if movie is None:
            movie = Movie(tmdb_id=data["id"])
            db.session.add(movie)

        release_date = None

        if data.get("release_date"):
            try:
                release_date = date.fromisoformat(
                    data["release_date"]
                )
            except ValueError:
                pass

        movie.title = data.get("title") or "Untitled"
        movie.original_title = data.get("original_title")
        movie.overview = data.get("overview")
        movie.release_date = release_date
        movie.poster_path = data.get("poster_path")
        movie.backdrop_path = data.get("backdrop_path")
        movie.original_language = data.get("original_language")
        movie.vote_average = data.get("vote_average")
        movie.vote_count = data.get("vote_count")
        movie.popularity = data.get("popularity")

        if data.get("runtime") is not None:
            movie.runtime = data["runtime"]

        movie.genres = [
            genre_map[genre_id]
            for genre_id in data.get("genre_ids", [])
            if genre_id in genre_map
        ]

        return movie

    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def rollback():
        db.session.rollback()