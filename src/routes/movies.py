from flask import Blueprint, current_app, jsonify, request
from datetime import date

from flask import abort
from flask_login import current_user, login_required
from sqlalchemy import select

from src.extensions import db
from src.models import Movie, WatchlistEntry
from src.repositories.movie_repository import MovieRepository
from src.services.notification_service import NotificationService
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

        result = get_movie_service().get_movies(category, page)

        return jsonify({
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
                        if movie.release_date else None
                    ),
                    "poster_path": movie.poster_path,
                    "backdrop_path": movie.backdrop_path,
                    "vote_average": movie.vote_average,
                    "popularity": movie.popularity,
                    "genres": [genre.name for genre in movie.genres],
                }
                for movie in result["movies"]
            ],
        })

    except TMDBError:
        current_app.logger.exception("TMDB request failed.")
        return jsonify({
            "error": "Movie service is temporarily unavailable."
        }), 502


@movies.get("/mood/<mood>")
def get_movies_by_mood(mood):
    allowed_moods = {
        "happy",
        "heartbroken",
        "romantic",
        "mind-blown",
        "melancholic",
        "motivated",
        "thrilled",
        "adventurous",
    }

    if mood not in allowed_moods:
        return jsonify({"error": "Invalid mood."}), 404

    page = request.args.get("page", 1, type=int)

    if page < 1:
        return jsonify({"error": "Invalid page number."}), 400

    try:
        result = get_movie_service().get_movies_by_mood(mood, page)

        return jsonify({
            "page": result.get("page", page),
            "total_pages": result.get("total_pages", 1),
            "total_results": result.get("total_results", 0),
            "movies": [
                {
                    "tmdb_id": movie["id"],
                    "title": movie.get("title"),
                    "overview": movie.get("overview"),
                    "release_date": movie.get("release_date"),
                    "poster_path": movie.get("poster_path"),
                    "backdrop_path": movie.get("backdrop_path"),
                    "vote_average": movie.get("vote_average"),
                    "genres": movie.get("genre_ids", []),
                }
                for movie in result.get("results", [])
            ],
        })

    except TMDBError:
        current_app.logger.exception(
            "TMDB mood recommendation request failed."
        )
        return jsonify({
            "error": "Mood recommendations are temporarily unavailable."
        }), 502


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

        return jsonify({
            "movie": {
                "id": movie.id,
                "tmdb_id": movie.tmdb_id,
                "title": movie.title,
                "original_title": movie.original_title,
                "overview": movie.overview,
                "release_date": (
                    movie.release_date.isoformat()
                    if movie.release_date else None
                ),
                "runtime": movie.runtime,
                "poster_path": movie.poster_path,
                "backdrop_path": movie.backdrop_path,
                "original_language": movie.original_language,
                "vote_average": movie.vote_average,
                "vote_count": movie.vote_count,
                "genres": [genre.name for genre in movie.genres],
            },
            "directors": directors,
            "cast": cast,
            "trailers": trailers,
            "recommendations": recommended_movies,
        })

    except TMDBError:
        current_app.logger.exception(
            "TMDB movie details request failed."
        )
        return jsonify({
            "error": "Movie details are temporarily unavailable."
        }), 502
        
@movies.post("/watchlist/<int:tmdb_id>")
@login_required
def add_to_watchlist(tmdb_id):
    service = get_movie_service()

    try:
        existing_movie = db.session.scalar(
            select(Movie).where(Movie.tmdb_id == tmdb_id)
        )

        if existing_movie is None:
            details = service.tmdb.get_movie_details(tmdb_id)


            genres = service.tmdb.get_movie_genres()

            genre_map = {
                genre["id"]: MovieRepository.get_or_create_genre(genre)
                for genre in genres
            }

            movie_data = dict(details)
            movie_data["genre_ids"] = [
                genre["id"] for genre in details.get("genres", [])
            ]

            movie = MovieRepository.save_movie(movie_data, genre_map)
            db.session.flush()

        else:
            movie = existing_movie


        existing_entry = db.session.scalar(
            select(WatchlistEntry).where(
                WatchlistEntry.user_id == current_user.id,
                WatchlistEntry.movie_id == movie.id,
            )
        )

        if existing_entry:
            db.session.rollback()
            return jsonify({
                "message": "Movie is already in your watchlist."
            }), 409

        entry = WatchlistEntry(
            user_id=current_user.id,
            movie_id=movie.id,
        )

        db.session.add(entry)

        if movie.release_date and movie.release_date > date.today():
            NotificationService.create(
                current_user.id,
                movie,
                "added_to_watchlist",
                f"{movie.title} was added to your upcoming watchlist.",
            )
        db.session.commit()

        return jsonify({
            "message": "Movie added to your watchlist.",
            "movie_id": movie.tmdb_id,
        }), 201

    except TMDBError:
        db.session.rollback()
        current_app.logger.exception("Unable to add movie to watchlist.")
        return jsonify({
            "error": "Movie service is temporarily unavailable."
        }), 502

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Watchlist operation failed.")
        return jsonify({
            "error": "Unable to update your watchlist."
        }), 500


@movies.delete("/watchlist/<int:tmdb_id>")
@login_required
def remove_from_watchlist(tmdb_id):
    movie = db.session.scalar(
        select(Movie).where(Movie.tmdb_id == tmdb_id)
    )

    if movie is None:
        return jsonify({"error": "Movie not found."}), 404

    entry = db.session.scalar(
        select(WatchlistEntry).where(
            WatchlistEntry.user_id == current_user.id,
            WatchlistEntry.movie_id == movie.id,
        )
    )

    if entry is None:
        return jsonify({
            "error": "Movie is not in your watchlist."
        }), 404

    db.session.delete(entry)
    db.session.commit()

    return jsonify({"message": "Movie removed from your watchlist."})