"""Import models so SQLAlchemy and Flask-Migrate discover all metadata."""

from .employee import Employee
from .salary import SalaryStructure
from .user import User, UserRole

__all__ = ["Employee", "SalaryStructure", "User", "UserRole"]
