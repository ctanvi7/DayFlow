"""Tests for the local demo Admin seeding command."""

import pytest

from app import create_app
from app.extensions import db
from app.models import User, UserRole
from scripts.seed_demo import SeedConfigurationError, seed_demo


def create_seed_app(password: str | None = "ChangeMe123!"):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "DEMO_ADMIN_LOGIN_ID": "OIADMIN",
            "DEMO_ADMIN_EMAIL": "admin@example.local",
            "DEMO_ADMIN_PASSWORD": password,
        }
    )
    with app.app_context():
        db.create_all()
    return app


def test_seed_creates_a_hashed_idempotent_admin():
    app = create_seed_app()

    assert seed_demo(app) == "Demo Admin created."
    assert seed_demo(app) == "Demo Admin already exists."

    with app.app_context():
        admins = User.query.filter_by(email="admin@example.local").all()
        assert len(admins) == 1
        admin = admins[0]
        assert admin.role == UserRole.ADMIN
        assert admin.must_change_password is False
        assert admin.is_active is True
        assert admin.password_hash != "ChangeMe123!"
        assert admin.check_password("ChangeMe123!")


def test_seed_requires_a_demo_password():
    app = create_seed_app(password=None)

    with pytest.raises(SeedConfigurationError, match="DEMO_ADMIN_PASSWORD"):
        seed_demo(app)
