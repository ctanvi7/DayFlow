"""Attendance persistence and business rules."""

from __future__ import annotations

from datetime import date, datetime
from typing import Callable

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.attendance import Attendance, PRESENT


class AttendanceError(Exception):
    status_code = 400


class AttendanceConflictError(AttendanceError):
    status_code = 409


class AttendanceNotFoundError(AttendanceError):
    status_code = 404


class AttendanceValidationError(AttendanceError):
    status_code = 400


class AttendanceService:
    """Owns database-backed attendance operations."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or datetime.now

    def check_in(self, employee_id: int) -> Attendance:
        now = self._clock()
        if self.get_today_attendance(employee_id, now.date()) is not None:
            raise AttendanceConflictError("Attendance has already been checked in today.")

        record = Attendance(
            employee_id=employee_id,
            attendance_date=now.date(),
            check_in_at=now,
            break_minutes=current_app.config["DEFAULT_BREAK_MINUTES"],
            status=PRESENT,
        )
        try:
            db.session.add(record)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise AttendanceConflictError(
                "Attendance has already been checked in today."
            ) from exc
        except Exception:
            db.session.rollback()
            raise
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
        record.work_minutes = self.calculate_work_minutes(record.check_in_at, now, record.break_minutes)
        record.extra_minutes = self.calculate_extra_minutes(record.work_minutes)
        record.status = PRESENT
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return record

    def get_employee_attendance(self, employee_id: int, year: int, month: int) -> list[Attendance]:
        if month < 1 or month > 12:
            raise AttendanceValidationError("month must be between 1 and 12.")
        start_date = date(year, month, 1)
        end_date = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        return (
            Attendance.query.filter(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date < end_date,
            )
            .order_by(Attendance.attendance_date.desc())
            .all()
        )

    def get_today_attendance(self, employee_id: int, attendance_date: date | None = None) -> Attendance | None:
        target_date = attendance_date or self._clock().date()
        return Attendance.query.filter_by(employee_id=employee_id, attendance_date=target_date).first()

    def get_all_attendance(self, filters: dict | None = None) -> list[Attendance]:
        filters = filters or {}
        query = Attendance.query
        if filters.get("employee_id"):
            try:
                query = query.filter_by(employee_id=int(filters["employee_id"]))
            except (TypeError, ValueError) as exc:
                raise AttendanceValidationError("employee_id must be an integer.") from exc
        if filters.get("status"):
            query = query.filter_by(status=str(filters["status"]).upper())
        return query.order_by(Attendance.attendance_date.desc()).all()

    @staticmethod
    def calculate_work_minutes(check_in_at: datetime, check_out_at: datetime, break_minutes: int) -> int:
        elapsed_minutes = int((check_out_at - check_in_at).total_seconds() // 60)
        return max(0, elapsed_minutes - max(0, break_minutes))

    @staticmethod
    def calculate_extra_minutes(work_minutes: int) -> int:
        return max(0, work_minutes - current_app.config["SCHEDULED_WORK_MINUTES"])
