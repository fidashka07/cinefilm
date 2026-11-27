from flask import Flask, render_template
from src.routes.profiles import profiles
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

@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(models.User, int(user_id))
    except (ValueError, TypeError):
        return None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.register_blueprint(notifications)
    
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
    @app.route("/")
    def index():
        return render_template("index.html")    
    def index():
        return """
        <h1>Welcome to CINEFILM</h1>
        <p>Your cinematic universe starts here.</p>
        """

    return app