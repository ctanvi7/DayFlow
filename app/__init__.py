from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv

from app.config import Config
from app.extensions import db
from app.routes.health_routes import health_bp
from app.routes.salary_routes import salary_bp

migrate = Migrate()


def create_app(config_class=Config):
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(health_bp)
    app.register_blueprint(salary_bp)
    with app.app_context():
        from app import models
    return app
