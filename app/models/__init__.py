"""Import models so SQLAlchemy and Flask-Migrate discover all metadata."""

from .attendance import Attendance
from .employee import Employee
from .leave import LeaveRequest
from .salary import SalaryStructure
from .user import User, UserRole

__all__ = ["Attendance", "Employee", "LeaveRequest", "SalaryStructure", "User", "UserRole"]
