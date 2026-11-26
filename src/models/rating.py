from datetime import UTC, datetime

from src.extensions import db


class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    movie_id = db.Column(
        db.Integer,
        db.ForeignKey("movies.id"),
        nullable=False,
    )

    score = db.Column(db.Float, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = db.relationship("User", back_populates="ratings")
    movie = db.relationship("Movie", back_populates="ratings")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "movie_id",
            name="unique_user_movie_rating",
        ),
        db.CheckConstraint(
            "score >= 0.5 AND score <= 5.0",
            name="valid_rating_score",
        ),
    )