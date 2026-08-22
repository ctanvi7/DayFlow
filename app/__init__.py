"""Dayflow application factory."""

from flask import Flask

from .config import Config
from .extensions import db, migrate


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Dayflow Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set in the environment.")

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models before Flask-Migrate inspects SQLAlchemy metadata.
    from .models import Employee, User  # noqa: F401
    from .routes.health_routes import health_bp

    app.register_blueprint(health_bp)

    return app
