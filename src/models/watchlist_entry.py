from datetime import UTC, datetime

from src.extensions import db


class WatchlistEntry(db.Model):
    __tablename__ = "watchlist_entries"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    movie_id = db.Column(
        db.Integer,
        db.ForeignKey("movies.id"),
        nullable=False,
        index=True,
    )

    added_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = db.relationship("User", back_populates="watchlist_entries")
    movie = db.relationship("Movie", back_populates="watchlist_entries")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "movie_id",
            name="unique_user_movie_watchlist",
        ),
    )