"""Import models so SQLAlchemy and Flask-Migrate discover all metadata."""

from .employee import Employee
from .user import User, UserRole

__all__ = ["Employee", "User", "UserRole"]

try:
    from .salary import SalaryStructure
except ModuleNotFoundError as exc:
    if exc.name != "app.models.salary":
        raise
else:
    __all__.append("SalaryStructure")
