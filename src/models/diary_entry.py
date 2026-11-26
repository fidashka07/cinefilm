from datetime import UTC, date, datetime

from src.extensions import db


class DiaryEntry(db.Model):
    __tablename__ = "diary_entries"

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

    watched_on = db.Column(db.Date, default=date.today, nullable=False)

    is_rewatch = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = db.relationship("User", back_populates="diary_entries")
    movie = db.relationship("Movie", back_populates="diary_entries")