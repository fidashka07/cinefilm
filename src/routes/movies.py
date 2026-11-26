from flask import Blueprint, current_app, jsonify, request

from src.services.movie_service import MovieService
from src.services.tmdb_client import TMDBClient, TMDBError

movies = Blueprint(
    "movies",
    __name__,
    url_prefix="/movies",
)


def get_movie_service():
    client = TMDBClient(
        token=current_app.config["TMDB_READ_ACCESS_TOKEN"],
        base_url=current_app.config["TMDB_BASE_URL"],
    )

    return MovieService(client)


@movies.get("/<category>")
def get_movies(category):
    allowed_categories = {
        "trending",
        "popular",
        "top-rated",
        "upcoming",
    }

    if category not in allowed_categories:
        return jsonify({"error": "Invalid movie category."}), 404

    try:
        page = request.args.get("page", 1, type=int)

        if page < 1:
            return jsonify({"error": "Invalid page number."}), 400

        result = get_movie_service().get_movies(
            category,
            page,
        )

        return jsonify(
            {
                "page": result["page"],
                "total_pages": result["total_pages"],
                "total_results": result["total_results"],
                "movies": [
                    {
                        "id": movie.id,
                        "tmdb_id": movie.tmdb_id,
                        "title": movie.title,
                        "overview": movie.overview,
                        "release_date": (
                            movie.release_date.isoformat()
                            if movie.release_date
                            else None
                        ),
                        "poster_path": movie.poster_path,
                        "backdrop_path": movie.backdrop_path,
                        "vote_average": movie.vote_average,
                        "popularity": movie.popularity,
                        "genres": [
                            genre.name for genre in movie.genres
                        ],
                    }
                    for movie in result["movies"]
                ],
            }
        )

    except TMDBError:
        current_app.logger.exception("TMDB request failed.")
        return jsonify(
            {"error": "Movie service is temporarily unavailable."}
        ), 502


@movies.get("/details/<int:tmdb_id>")
def get_movie_details(tmdb_id):
    try:
        result = get_movie_service().get_movie_details(tmdb_id)

        movie = result["movie"]
        credits = result["credits"]
        videos = result["videos"]
        recommendations = result["recommendations"]

        directors = [
            person["name"]
            for person in credits.get("crew", [])
            if person.get("job") == "Director"
        ]

        cast = [
            {
                "name": person["name"],
                "character": person.get("character"),
                "profile_path": person.get("profile_path"),
            }
            for person in credits.get("cast", [])[:12]
        ]

        trailers = [
            {
                "name": video["name"],
                "key": video["key"],
                "site": video["site"],
            }
            for video in videos.get("results", [])
            if video.get("site") == "YouTube"
            and video.get("type") == "Trailer"
        ]

        recommended_movies = [
            {
                "tmdb_id": item["id"],
                "title": item["title"],
                "poster_path": item.get("poster_path"),
                "vote_average": item.get("vote_average"),
                "release_date": item.get("release_date"),
            }
            for item in recommendations.get("results", [])[:12]
        ]

        return jsonify(
            {
                "movie": {
                    "id": movie.id,
                    "tmdb_id": movie.tmdb_id,
                    "title": movie.title,
                    "original_title": movie.original_title,
                    "overview": movie.overview,
                    "release_date": (
                        movie.release_date.isoformat()
                        if movie.release_date
                        else None
                    ),
                    "runtime": movie.runtime,
                    "poster_path": movie.poster_path,
                    "backdrop_path": movie.backdrop_path,
                    "original_language": movie.original_language,
                    "vote_average": movie.vote_average,
                    "vote_count": movie.vote_count,
                    "genres": [
                        genre.name for genre in movie.genres
                    ],
                },
                "directors": directors,
                "cast": cast,
                "trailers": trailers,
                "recommendations": recommended_movies,
            }
        )

    except TMDBError:
        current_app.logger.exception(
            "TMDB movie details request failed."
        )
        return jsonify(
            {"error": "Movie details are temporarily unavailable."}
        ), 502