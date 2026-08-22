"""Temporary in-memory attendance business logic."""

from datetime import datetime
from typing import Callable, Optional

from app.models.attendance import Attendance, PRESENT


BREAK_MINUTES = 60
SCHEDULED_WORK_MINUTES = 480


class AttendanceError(Exception):
    """Base error for expected attendance workflow failures."""

    status_code = 400


class AttendanceConflictError(AttendanceError):
    status_code = 409


class AttendanceNotFoundError(AttendanceError):
    status_code = 404


class AttendanceValidationError(AttendanceError):
    status_code = 400


class AttendanceService:
    """Provides attendance operations until the database layer is available."""

    # TODO(Member 2): Replace in-memory repository with SQLAlchemy after Member 4 database foundation is merged.
    def __init__(self, clock: Optional[Callable[[], datetime]] = None) -> None:
        self._records: list[Attendance] = []
        self._next_id = 1
        self._clock = clock or datetime.now

    def check_in(self, employee_id: int) -> Attendance:
        now = self._clock()
        if self.get_today_attendance(employee_id, now.date()):
            raise AttendanceConflictError("Attendance has already been checked in today.")

        record = Attendance(
            id=self._next_id,
            employee_id=employee_id,
            attendance_date=now.date(),
            check_in_at=now,
            check_out_at=None,
            break_minutes=BREAK_MINUTES,
            status=PRESENT,
        )
        self._records.append(record)
        self._next_id += 1
        return record

    def check_out(self, employee_id: int) -> Attendance:
        now = self._clock()
        record = self.get_today_attendance(employee_id, now.date())
        if record is None:
            raise AttendanceNotFoundError("No attendance check-in exists for today.")
        if record.check_out_at is not None:
            raise AttendanceConflictError("Attendance has already been checked out today.")
        if record.check_in_at is None or now < record.check_in_at:
            raise AttendanceValidationError("Check-out time cannot be earlier than check-in time.")

        record.check_out_at = now
        record.work_minutes = self.calculate_work_minutes(
            record.check_in_at, record.check_out_at, record.break_minutes
        )
        record.extra_minutes = self.calculate_extra_minutes(record.work_minutes)
        record.status = PRESENT
        return record

    def get_employee_attendance(self, employee_id: int, year: int, month: int) -> list[Attendance]:
        return [
            record
            for record in self._records
            if record.employee_id == employee_id
            and record.attendance_date.year == year
            and record.attendance_date.month == month
        ]

    def get_today_attendance(self, employee_id: int, attendance_date=None) -> Optional[Attendance]:
        target_date = attendance_date or self._clock().date()
        return next(
            (
                record
                for record in self._records
                if record.employee_id == employee_id and record.attendance_date == target_date
            ),
            None,
        )

    def get_all_attendance(self) -> list[Attendance]:
        return list(self._records)

    @staticmethod
    def calculate_work_minutes(check_in_at: datetime, check_out_at: datetime, break_minutes: int) -> int:
        elapsed_minutes = int((check_out_at - check_in_at).total_seconds() // 60)
        return max(0, elapsed_minutes - break_minutes)

    @staticmethod
    def calculate_extra_minutes(work_minutes: int) -> int:
        return max(0, work_minutes - SCHEDULED_WORK_MINUTES)
