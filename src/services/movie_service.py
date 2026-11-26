from src.repositories.movie_repository import MovieRepository


class MovieService:
    """Coordinates TMDB data retrieval and database persistence."""

    def __init__(self, tmdb_client):
        self.tmdb = tmdb_client

    def get_movies(self, category, page=1):
        if page < 1:
            raise ValueError("Page must be greater than zero.")

        response = self.tmdb.get_movies(category, page)

        try:
            genres = self.tmdb.get_movie_genres()

            genre_map = {}

            for genre_data in genres:
                genre = MovieRepository.get_or_create_genre(
                    genre_data
                )
                genre_map[genre.tmdb_id] = genre

            movies = [
                MovieRepository.save_movie(movie, genre_map)
                for movie in response.get("results", [])
            ]

            MovieRepository.commit()

            return {
                "movies": movies,
                "page": response.get("page", page),
                "total_pages": response.get("total_pages", 1),
                "total_results": response.get("total_results", 0),
            }

        except Exception:
            MovieRepository.rollback()
            raise