from datetime import UTC, datetime

from src.extensions import db
from src.models.associations import movie_genres


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)

    tmdb_id = db.Column(
        db.Integer,
        unique=True,
        nullable=False,
        index=True,
    )

    title = db.Column(db.String(255), nullable=False)
    original_title = db.Column(db.String(255))

    overview = db.Column(db.Text)
    release_date = db.Column(db.Date)
    runtime = db.Column(db.Integer)

    poster_path = db.Column(db.String(500))
    backdrop_path = db.Column(db.String(500))

    original_language = db.Column(db.String(10))

    vote_average = db.Column(db.Float)
    vote_count = db.Column(db.Integer)
    popularity = db.Column(db.Float)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    genres = db.relationship(
        "Genre",
        secondary=movie_genres,
        back_populates="movies",
    )

    reviews = db.relationship(
        "Review",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    ratings = db.relationship(
        "Rating",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    diary_entries = db.relationship(
        "DiaryEntry",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    watchlist_entries = db.relationship(
        "WatchlistEntry",
        back_populates="movie",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Movie {self.title}>"
