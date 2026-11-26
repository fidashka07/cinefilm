from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Database
db = SQLAlchemy()

# Database migrations
migrate = Migrate()

# User authentication
login_manager = LoginManager()

# CSRF protection
csrf = CSRFProtect()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)