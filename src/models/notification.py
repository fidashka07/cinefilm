from datetime import UTC, datetime

from src.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    movie_id = db.Column(
        db.Integer,
        db.ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    notification_type = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(255), nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    read_at = db.Column(db.DateTime(timezone=True))

    user = db.relationship("User", back_populates="notifications")
    movie = db.relationship("Movie", back_populates="notifications")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "movie_id",
            "notification_type",
            name="uq_notification_user_movie_type",
        ),
    )
