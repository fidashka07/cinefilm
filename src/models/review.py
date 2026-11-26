from datetime import UTC, datetime

from src.extensions import db


class Review(db.Model):
    __tablename__ = "reviews"

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

    content = db.Column(db.Text, nullable=False)
    contains_spoilers = db.Column(db.Boolean, default=False, nullable=False)

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

    user = db.relationship("User", back_populates="reviews")
    movie = db.relationship("Movie", back_populates="reviews")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "movie_id",
            name="unique_user_movie_review",
        ),
    )