"""Environment-backed application configuration."""

import os

from dotenv import load_dotenv

load_dotenv()


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable, falling back safely for development."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dayflow_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    COMPANY_CODE = os.getenv("COMPANY_CODE", "OI")
    COMPANY_NAME = os.getenv("COMPANY_NAME", "Odoo India")
    DEFAULT_BREAK_MINUTES = _env_int("DEFAULT_BREAK_MINUTES", 60)
    SCHEDULED_WORK_MINUTES = _env_int("SCHEDULED_WORK_MINUTES", 480)
    WORKING_DAYS = tuple(range(5))
    ATTENDANCE_DECISION_HOUR = _env_int("ATTENDANCE_DECISION_HOUR", 9)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

    DEMO_ADMIN_EMAIL = os.getenv("DEMO_ADMIN_EMAIL", "admin@example.local")
    DEMO_ADMIN_LOGIN_ID = os.getenv("DEMO_ADMIN_LOGIN_ID", "OIADMIN")
    DEMO_ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD")
