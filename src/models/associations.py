from src.extensions import db

movie_genres = db.Table(
    "movie_genres",
    db.Column(
        "movie_id",
        db.Integer,
        db.ForeignKey("movies.id"),
        primary_key=True,
    ),
    db.Column(
        "genre_id",
        db.Integer,
        db.ForeignKey("genres.id"),
        primary_key=True,
    ),
)

user_follows = db.Table(
    "user_follows",
    db.Column(
        "follower_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "followed_id",
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)