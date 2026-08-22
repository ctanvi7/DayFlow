"""Leave business rules and database transactions owned by Member 3."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import or_

from app.extensions import db
from app.models.leave import LeaveRequest


class LeaveValidationError(ValueError):
    def __init__(self, errors: dict[str, str]):
        super().__init__("Validation failed")
        self.errors = errors


class LeaveConflictError(ValueError):
    pass


class LeaveNotFoundError(LookupError):
    pass


def _parse_date(value: object, field: str) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise LeaveValidationError(
            {field: "Use ISO date format YYYY-MM-DD"}
        ) from exc


def validate_submission(payload: dict) -> dict:
    """Normalize permitted employee input; ignore client-controlled fields."""
    payload = payload or {}
    errors: dict[str, str] = {}
    leave_type = str(payload.get("leave_type", "")).strip().upper()
    remarks = str(payload.get("remarks", "")).strip()
    start_date = _parse_date(payload.get("start_date"), "start_date")
    end_date = _parse_date(payload.get("end_date"), "end_date")

    if leave_type not in LeaveRequest.LEAVE_TYPES:
        errors["leave_type"] = "Leave type must be PAID, SICK, or UNPAID"
    if not start_date:
        errors["start_date"] = "Start date is required"
    if not end_date:
        errors["end_date"] = "End date is required"
    if start_date and end_date and start_date > end_date:
        errors["start_date"] = "Start date cannot be after end date"
    if not remarks:
        errors["remarks"] = "Remarks are required"
    elif len(remarks) > 500:
        errors["remarks"] = "Remarks cannot exceed 500 characters"
    if errors:
        raise LeaveValidationError(errors)

    return {
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "days_requested": Decimal((end_date - start_date).days + 1),
        "remarks": remarks,
    }


def _find_overlap(
    employee_id: int, start_date: date, end_date: date
) -> LeaveRequest | None:
    return (
        LeaveRequest.query.filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_(("PENDING", "APPROVED")),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
        .order_by(LeaveRequest.start_date.asc())
        .first()
    )


def create_leave_request(employee_id: int, payload: dict) -> LeaveRequest:
    values = validate_submission(payload)
    if _find_overlap(employee_id, values["start_date"], values["end_date"]):
        raise LeaveConflictError(
            "This request overlaps an existing pending or approved leave"
        )

    request = LeaveRequest(employee_id=employee_id, status="PENDING", **values)
    try:
        db.session.add(request)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return request


def list_own_leave_requests(employee_id: int) -> list[LeaveRequest]:
    return (
        LeaveRequest.query.filter_by(employee_id=employee_id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )


def list_leave_requests(filters: dict) -> list[LeaveRequest]:
    """Return Admin/HR requests using supported, server-controlled filters."""
    query = LeaveRequest.query
    status = str(filters.get("status", "")).upper()
    leave_type = str(filters.get("leave_type", "")).upper()
    search = str(filters.get("search", "")).strip()

    if status in LeaveRequest.STATUSES:
        query = query.filter(LeaveRequest.status == status)
    if leave_type in LeaveRequest.LEAVE_TYPES:
        query = query.filter(LeaveRequest.leave_type == leave_type)
    if filters.get("employee_id"):
        try:
            query = query.filter(
                LeaveRequest.employee_id == int(filters["employee_id"])
            )
        except (TypeError, ValueError):
            raise LeaveValidationError(
                {"employee_id": "Employee ID must be a number"}
            )
    filter_start = _parse_date(filters.get("start_date"), "start_date")
    filter_end = _parse_date(filters.get("end_date"), "end_date")
    if filter_start:
        query = query.filter(LeaveRequest.end_date >= filter_start)
    if filter_end:
        query = query.filter(LeaveRequest.start_date <= filter_end)
    if filter_start and filter_end and filter_start > filter_end:
        raise LeaveValidationError(
            {"start_date": "Start date cannot be after end date"}
        )
    if search:
        # Employee is supplied by Member 1; import lazily to avoid a cycle.
        from app.models.employee import Employee

        pattern = f"%{search}%"
        query = query.join(Employee).filter(
            or_(
                Employee.first_name.ilike(pattern),
                Employee.last_name.ilike(pattern),
            )
        )
    return query.order_by(LeaveRequest.created_at.desc()).all()


def decide_leave_request(
    request_id: int, reviewer_user_id: int, payload: dict
) -> LeaveRequest:
    request = db.session.get(LeaveRequest, request_id)
    if request is None:
        raise LeaveNotFoundError("Leave request not found")
    if request.status != "PENDING":
        raise LeaveConflictError("A reviewed leave request cannot be changed")

    decision = str((payload or {}).get("status", "")).upper()
    comment = str((payload or {}).get("review_comment", "")).strip()
    errors = {}
    if decision not in ("APPROVED", "REJECTED"):
        errors["status"] = "Decision must be APPROVED or REJECTED"
    if len(comment) > 500:
        errors["review_comment"] = (
            "Review comment cannot exceed 500 characters"
        )
    if errors:
        raise LeaveValidationError(errors)

    request.status = decision
    request.review_comment = comment or None
    request.reviewed_by_user_id = reviewer_user_id
    request.reviewed_at = datetime.utcnow()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return request
