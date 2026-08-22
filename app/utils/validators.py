"""Input validation helpers for Dayflow API routes."""

from datetime import date
import re
import string
from typing import Any

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _required_text(value: Any, field_name: str, max_length: int) -> tuple[str | None, str | None]:
    if not isinstance(value, str) or not (normalized := value.strip()):
        return None, f"{field_name} is required."
    if len(normalized) > max_length:
        return None, f"{field_name} cannot exceed {max_length} characters."
    return normalized, None


def validate_employee_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate and normalize the minimum data needed to create an employee."""
    data: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for field_name, max_length in (("first_name", 80), ("last_name", 80)):
        value, error = _required_text(payload.get(field_name), field_name.replace("_", " ").title(), max_length)
        if error:
            errors[field_name] = error
        elif not any(character.isalpha() for character in value):
            errors[field_name] = f"{field_name.replace('_', ' ').title()} must include a letter."
        else:
            data[field_name] = value

    email = payload.get("email")
    if not isinstance(email, str) or not (normalized_email := email.strip().lower()):
        errors["email"] = "Email is required."
    elif len(normalized_email) > 255 or not EMAIL_PATTERN.fullmatch(normalized_email):
        errors["email"] = "Enter a valid email address."
    else:
        data["email"] = normalized_email

    for field_name, max_length in (("department", 100), ("job_title", 100)):
        value, error = _required_text(payload.get(field_name), field_name.replace("_", " ").title(), max_length)
        if error:
            errors[field_name] = error
        else:
            data[field_name] = value

    joining_date = payload.get("date_of_joining")
    if not isinstance(joining_date, str):
        errors["date_of_joining"] = "Date of joining is required in ISO format."
    else:
        try:
            data["date_of_joining"] = date.fromisoformat(joining_date)
        except ValueError:
            errors["date_of_joining"] = "Date of joining must be a valid ISO date."

    for field_name, max_length in (("phone", 20), ("company", 160), ("location", 160), ("manager_name", 160)):
        value = payload.get(field_name)
        if value is not None:
            if not isinstance(value, str) or len(value.strip()) > max_length:
                errors[field_name] = f"{field_name.replace('_', ' ').title()} must be at most {max_length} characters."
            else:
                data[field_name] = value.strip() or None

    return data, errors


def password_errors(password: Any, field_name: str = "new_password") -> dict[str, str]:
    """Return field errors when a password does not satisfy the shared policy."""
    if not isinstance(password, str) or not password:
        return {field_name: "Password is required."}
    if len(password) < 8:
        return {field_name: "Password must be at least 8 characters long."}
    if not any(character.isupper() for character in password):
        return {field_name: "Password must include an uppercase letter."}
    if not any(character.islower() for character in password):
        return {field_name: "Password must include a lowercase letter."}
    if not any(character.isdigit() for character in password):
        return {field_name: "Password must include a number."}
    if not any(character in string.punctuation for character in password):
        return {field_name: "Password must include a symbol."}
    return {}
