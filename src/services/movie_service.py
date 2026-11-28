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
        
    def search_movies(self, query, page=1):
        query = query.strip()

        if not query:
            raise ValueError("Search query cannot be empty.")

        if page < 1:
            raise ValueError("Page must be greater than zero.")

        return self.tmdb.search_movies(query, page)
    
    def get_movie_details(self, tmdb_id):
        try:
            data = self.tmdb.get_movie_details(tmdb_id)

            genre_map = {}

            for genre_data in data.get("genres", []):
                genre = MovieRepository.get_or_create_genre(genre_data)
                genre_map[genre.tmdb_id] = genre

            movie_data = {
                **data,
                "genre_ids": [
                    genre["id"] for genre in data.get("genres", [])
                ],
            }

            movie = MovieRepository.save_movie(movie_data, genre_map)

            MovieRepository.commit()

            return {
                "movie": movie,
                "credits": data.get("credits", {}),
                "videos": data.get("videos", {}),
                "recommendations": data.get("recommendations", {}),
            }

        except Exception:
            MovieRepository.rollback()
            raise

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

        for name in (user.favorite_genres or []):
            normalized = name.strip().casefold()

            if normalized and normalized not in preferred_genres:
                preferred_genres.append(normalized)

        for rating in user.ratings:
            if rating.score >= 8.0 and rating.movie:
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

        # Collect recommendations based on the user's Top 5 movies.
        top_movie_recommendations = []
        processed_tmdb_ids = set()

        for title in (user.top_movies or [])[:5]:
            title = title.strip()

            if not title:
                continue

            search_result = self.tmdb.search_movies(title)
            search_results = search_result.get("results", [])

            if not search_results:
                continue

            tmdb_id = search_results[0]["id"]

            if tmdb_id in processed_tmdb_ids:
                continue

            processed_tmdb_ids.add(tmdb_id)

            recommendations = self.tmdb.get_movie_recommendations(
                tmdb_id,
                page=page,
            )

            top_movie_recommendations.extend(
                recommendations.get("results", [])
            )

        # Exclude movies already rated or added to the watchlist.
        excluded_ids = {
            rating.movie.tmdb_id
            for rating in user.ratings
            if rating.movie
        }

        excluded_ids.update(
            entry.movie.tmdb_id
            for entry in user.watchlist_entries
            if entry.movie
        )

        # Combine both recommendation sources without duplicates.
        combined_results = []
        seen_ids = set()

        for movie in (
            top_movie_recommendations
            + response.get("results", [])
        ):
            movie_id = movie["id"]

            if movie_id in excluded_ids or movie_id in seen_ids:
                continue

            seen_ids.add(movie_id)
            combined_results.append(movie)

        response["results"] = combined_results[:20]
        
        return response