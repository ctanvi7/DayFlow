"""Temporary attendance data representation.

This model deliberately has no persistence dependency while the shared
SQLAlchemy foundation is still being built.
"""

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Optional


PRESENT = "PRESENT"
ABSENT = "ABSENT"
HALF_DAY = "HALF_DAY"
LEAVE = "LEAVE"


@dataclass
class Attendance:
    id: int
    employee_id: int
    attendance_date: date
    check_in_at: Optional[datetime]
    check_out_at: Optional[datetime]
    break_minutes: int
    work_minutes: int = 0
    extra_minutes: int = 0
    status: str = PRESENT

    def to_dict(self) -> dict:
        """Return a JSON-safe representation for the temporary API."""
        data = asdict(self)
        data["attendance_date"] = self.attendance_date.isoformat()
        data["check_in_at"] = self.check_in_at.isoformat() if self.check_in_at else None
        data["check_out_at"] = self.check_out_at.isoformat() if self.check_out_at else None
        return data
