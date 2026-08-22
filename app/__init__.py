"""Dayflow application factory."""

from flask import Flask

from .config import Config
from .extensions import db, migrate


def create_app(config_override: dict | type[Config] | None = None) -> Flask:
    """Create and configure the shared Dayflow application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    if isinstance(config_override, dict):
        app.config.update(config_override)
    elif config_override is not None:
        app.config.from_object(config_override)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY must be set in the environment.")

    db.init_app(app)
    migrate.init_app(app, db)

    # Import every current model before Flask-Migrate inspects SQLAlchemy metadata.
    from . import models  # noqa: F401
    from .routes.auth_routes import auth_bp
    from .routes.employee_routes import employee_bp
    from .routes.health_routes import health_bp
    from .routes.salary_routes import salary_bp

    for blueprint in (health_bp, auth_bp, employee_bp, salary_bp):
        if blueprint.name not in app.blueprints:
            app.register_blueprint(blueprint)

    return app
