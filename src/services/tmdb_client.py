import time

import requests


class TMDBError(Exception):
    """Raised when TMDB API communication fails."""


class TMDBClient:
    """Adapter responsible for communicating with TMDB."""

    def __init__(self, token, base_url, timeout=10):
        if not token:
            raise ValueError("TMDB Read Access Token is missing.")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "accept": "application/json",
            }
        )

        self._cache = {}

    def get(self, endpoint, params=None, cache_seconds=300):
        params = params or {}

        cache_key = (endpoint, tuple(sorted(params.items())))
        cached = self._cache.get(cache_key)

        if cached and cached["expires"] > time.monotonic():
            return cached["data"]

        try:
            response = self.session.get(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

        except requests.RequestException as exc:
            raise TMDBError(
                "Unable to communicate with TMDB."
            ) from exc

        except ValueError as exc:
            raise TMDBError(
                "TMDB returned an invalid JSON response."
            ) from exc

        self._cache[cache_key] = {
            "data": data,
            "expires": time.monotonic() + cache_seconds,
        }

        return data

    def get_movie_genres(self):
        return self.get("genre/movie/list").get("genres", [])

    def get_movie_details(self, tmdb_id):
        return self.get(
            f"movie/{tmdb_id}",
            params={
                "append_to_response": "credits,videos,recommendations"
            },
    )
        
    def get_movies(self, category, page=1):
        endpoints = {
            "trending": "trending/movie/week",
            "popular": "movie/popular",
            "top-rated": "movie/top_rated",
            "upcoming": "movie/upcoming",
        }

        if category not in endpoints:
            raise ValueError("Invalid movie category.")

        return self.get(
            endpoints[category],
            params={"page": page},
        )
    def discover_movies(self, params=None):
        return self.get(
            "discover/movie",
            params=params or {},
        )