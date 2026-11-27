from src.repositories.movie_repository import MovieRepository


MOOD_GENRES = {
    "happy": "35",
    "heartbroken": "18",
    "romantic": "10749",
    "mind-blown": "9648|53",
    "melancholic": "18|14",
    "motivated": "18|12",
    "thrilled": "53|27",
    "adventurous": "12|14",
}


class MovieService:
    """Coordinates TMDB data retrieval and database persistence."""

    def __init__(self, tmdb_client):
        self.tmdb = tmdb_client

    def get_movie_details(self, tmdb_id):
        return self.tmdb.get_movie_details(tmdb_id)

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

    def get_movies_by_mood(self, mood, page=1):
        if mood not in MOOD_GENRES:
            raise ValueError("Invalid mood.")

        if page < 1:
            raise ValueError("Page must be greater than zero.")

        return self.tmdb.discover_movies({
            "with_genres": MOOD_GENRES[mood],
            "sort_by": "popularity.desc",
            "include_adult": False,
            "vote_count.gte": 50,
            "page": page,
        })

    def get_movies_for_user(self, user, page=1):
        if page < 1:
            raise ValueError("Page must be greater than zero.")

        genres = self.tmdb.get_movie_genres()

        genre_ids = {
            genre["name"].strip().casefold(): genre["id"]
            for genre in genres
        }

        preferred_genres = []

        # Add the user's selected favorite genres first.
        for name in (user.favorite_genres or []):
            normalized = name.strip().casefold()

            if normalized and normalized not in preferred_genres:
                preferred_genres.append(normalized)

        # Add genres from movies rated 4 stars or higher.
        for rating in user.ratings:
            if rating.score >= 4.0 and rating.movie:
                for genre in rating.movie.genres:
                    normalized = genre.name.strip().casefold()

                    if normalized and normalized not in preferred_genres:
                        preferred_genres.append(normalized)

        selected_ids = [
            genre_ids[name]
            for name in preferred_genres
            if name in genre_ids
        ]

        params = {
            "sort_by": "popularity.desc",
            "include_adult": False,
            "vote_count.gte": 50,
            "page": page,
        }

        if selected_ids:
            params["with_genres"] = "|".join(
                str(genre_id) for genre_id in selected_ids
            )

        response = self.tmdb.discover_movies(params)

        # Exclude movies the user has already rated.
        excluded_ids = {
            rating.movie.tmdb_id
            for rating in user.ratings
            if rating.movie
        }

        # Exclude movies already in the user's watchlist.
        excluded_ids.update(
            entry.movie.tmdb_id
            for entry in user.watchlist_entries
            if entry.movie
        )

        response["results"] = [
            movie
            for movie in response.get("results", [])
            if movie["id"] not in excluded_ids
        ]

        return response