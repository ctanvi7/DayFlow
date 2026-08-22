from datetime import date, datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensions import db
from app.models import Attendance, Employee, SalaryStructure
from app.services.salary_service import calculate_salary


class DataTransactionError(Exception):
    """Expected database failure with API-safe details."""

    def __init__(self, message, errors):
        super().__init__(message)
        self.errors = errors


def _database_error(exc):
    detail = str(getattr(exc, "orig", exc)).splitlines()[0]
    return DataTransactionError(
        "Database transaction failed", {"database": detail}
    )


class DataService:
    @staticmethod
    def update_salary(employee_id, updated_by_user_id, monthly_wage):
        try:
            employee = db.session.get(Employee, employee_id)
            if employee is None:
                raise DataTransactionError(
                    "Database transaction failed", {"employee_id": "Employee not found"}
                )
            values = calculate_salary(monthly_wage)
            salary = employee.salary or SalaryStructure(employee_id=employee_id)
            for field, value in values.items():
                setattr(salary, field, value)
            salary.updated_by_user_id = updated_by_user_id
            db.session.add(salary)
            db.session.commit()
            return salary
        except DataTransactionError:
            db.session.rollback()
            raise
        except (SQLAlchemyError, ValueError, TypeError) as exc:
            db.session.rollback()
            if isinstance(exc, (ValueError, TypeError)):
                raise DataTransactionError(
                    "Database transaction failed", {"database": str(exc)}
                ) from exc
            raise _database_error(exc) from exc

    @staticmethod
    def check_in(employee_id, attendance_date=None, checked_in_at=None, break_minutes=0):
        target_date = attendance_date or date.today()
        timestamp = checked_in_at or datetime.now()
        if not isinstance(target_date, date):
            raise DataTransactionError(
                "Database transaction failed", {"attendance_date": "Invalid date"}
            )
        try:
            employee = db.session.get(Employee, employee_id)
            if employee is None:
                raise DataTransactionError(
                    "Database transaction failed", {"employee_id": "Employee not found"}
                )
            existing = (
                db.session.query(Attendance)
                .filter_by(employee_id=employee_id, attendance_date=target_date)
                .with_for_update()
                .first()
            )
            if existing is not None:
                raise DataTransactionError(
                    "Database transaction failed",
                    {"attendance": "Employee has already checked in for this date"},
                )
            record = Attendance(
                employee_id=employee_id,
                attendance_date=target_date,
                check_in_at=timestamp,
                break_minutes=break_minutes,
                status="PRESENT",
            )
            db.session.add(record)
            db.session.commit()
            return record
        except DataTransactionError:
            db.session.rollback()
            raise
        except IntegrityError as exc:
            db.session.rollback()
            raise DataTransactionError(
                "Database transaction failed",
                {"attendance": "Employee has already checked in for this date"},
            ) from exc
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise _database_error(exc) from exc
