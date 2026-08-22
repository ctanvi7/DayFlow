"""Import models so SQLAlchemy and Flask-Migrate discover all metadata."""

from .employee import Employee
from .user import User, UserRole

__all__ = ["Employee", "User", "UserRole"]
