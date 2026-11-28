from flask import Flask, render_template

from src import models
from src.config import Config
from src.extensions import (
    csrf,
    db,
    limiter,
    login_manager,
    migrate,
)
from src.routes.auth import auth
from src.routes.movies import movies
from src.routes.notifications import notifications
from src.routes.profiles import profiles


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(models.User, int(user_id))
    except (ValueError, TypeError):
        return None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    app.register_blueprint(auth)
    app.register_blueprint(movies)
    app.register_blueprint(profiles)
    app.register_blueprint(notifications)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/greet/<name>")
    def greet(name):
        """Returns a personalized greeting."""
        return f"Hello, {name}!"

    return app