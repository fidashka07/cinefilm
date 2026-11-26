import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///cinefilm.db",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # TMDB API Read Access Token (v4)
    TMDB_READ_ACCESS_TOKEN = (
        os.getenv("TMDB_READ_ACCESS_TOKEN")
        or os.getenv("TMDB_API_KEY")
    )

    TMDB_BASE_URL = "https://api.themoviedb.org/3"

    WTF_CSRF_ENABLED = True