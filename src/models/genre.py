from src.extensions import db
from src.models.associations import movie_genres


class Genre(db.Model):
    __tablename__ = "genres"

    id = db.Column(db.Integer, primary_key=True)

    tmdb_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(100), unique=True, nullable=False)

    movies = db.relationship(
        "Movie",
        secondary=movie_genres,
        back_populates="genres",
    )

    def __repr__(self):
        return f"<Genre {self.name}>"