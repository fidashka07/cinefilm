from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from src.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    display_name = db.Column(db.String(60))
    bio = db.Column(db.String(500))
    avatar_url = db.Column(db.String(500))

    website_url = db.Column(db.String(500))
    instagram_url = db.Column(db.String(500))

    favorite_genres = db.Column(db.JSON, default=list, nullable=False)
    top_movies = db.Column(db.JSON, default=list, nullable=False)
    top_actors = db.Column(db.JSON, default=list, nullable=False)

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

    reviews = db.relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    ratings = db.relationship(
        "Rating",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    diary_entries = db.relationship(
        "DiaryEntry",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    watchlist_entries = db.relationship(
        "WatchlistEntry",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"