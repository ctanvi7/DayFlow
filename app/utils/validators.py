"""Input validation helpers for Dayflow API routes."""

from datetime import date
import re
import string
from typing import Any

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^\+?[0-9(). -]+$")

EMPLOYEE_PROFILE_FIELDS = frozenset(
    {
        "first_name",
        "last_name",
        "phone",
        "date_of_birth",
        "gender",
        "nationality",
        "marital_status",
        "department",
        "job_title",
        "manager_name",
        "company",
        "location",
        "date_of_joining",
        "address",
        "personal_email",
        "pan_no",
        "uan_no",
        "bank_account_no",
        "bank_name",
        "ifsc_code",
        "profile_image_path",
    }
)

EMPLOYEE_SELF_EDITABLE_FIELDS = frozenset(
    {"phone", "address", "personal_email", "profile_image_path"}
)

PROTECTED_PROFILE_FIELDS = frozenset(
    {
        "id",
        "user_id",
        "login_id",
        "email",
        "password",
        "password_hash",
        "role",
        "is_active",
        "must_change_password",
        "salary",
        "salary_structure",
        "monthly_wage",
        "basic_amount",
        "hra_amount",
        "standard_allowance",
        "performance_bonus",
        "lta_amount",
        "fixed_allowance",
        "employee_pf",
        "employer_pf",
        "professional_tax",
        "created_at",
        "updated_at",
    }
)


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


def validate_employee_profile_update(
    payload: dict[str, Any], allowed_fields: frozenset[str],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate profile edits and reject unknown or unauthorized fields."""
    data: dict[str, Any] = {}
    errors: dict[str, str] = {}

    if not payload:
        return data, {"body": "Provide at least one profile field to update."}

    for field_name, value in payload.items():
        if field_name in PROTECTED_PROFILE_FIELDS or field_name in EMPLOYEE_PROFILE_FIELDS:
            if field_name not in allowed_fields:
                errors[field_name] = "This field cannot be updated through the employee profile."
            continue
        errors[field_name] = "Unknown profile field."

    for field_name in allowed_fields.intersection(payload):
        value = payload[field_name]
        if field_name in {"first_name", "last_name", "department", "job_title"}:
            max_length = {"first_name": 80, "last_name": 80, "department": 100, "job_title": 100}[field_name]
            normalized, error = _required_text(value, field_name.replace("_", " ").title(), max_length)
            if error:
                errors[field_name] = error
            elif field_name in {"first_name", "last_name"} and not any(character.isalpha() for character in normalized):
                errors[field_name] = f"{field_name.replace('_', ' ').title()} must include a letter."
            else:
                data[field_name] = normalized
        elif field_name == "phone":
            if value is None or (isinstance(value, str) and not value.strip()):
                data[field_name] = None
            elif not isinstance(value, str) or len(value.strip()) > 20 or not PHONE_PATTERN.fullmatch(value.strip()):
                errors[field_name] = "Enter a valid phone number."
            elif sum(character.isdigit() for character in value) < 7:
                errors[field_name] = "Phone number must contain at least 7 digits."
            else:
                data[field_name] = value.strip()
        elif field_name == "personal_email":
            if value is None or (isinstance(value, str) and not value.strip()):
                data[field_name] = None
            elif not isinstance(value, str) or len(value.strip()) > 255 or not EMAIL_PATTERN.fullmatch(value.strip().lower()):
                errors[field_name] = "Enter a valid personal email address."
            else:
                data[field_name] = value.strip().lower()
        elif field_name in {"date_of_birth", "date_of_joining"}:
            if value is None and field_name == "date_of_birth":
                data[field_name] = None
            elif not isinstance(value, str):
                errors[field_name] = "Enter a valid ISO date."
            else:
                try:
                    parsed = date.fromisoformat(value)
                except ValueError:
                    errors[field_name] = "Enter a valid ISO date."
                else:
                    if field_name == "date_of_birth" and parsed > date.today():
                        errors[field_name] = "Date of birth cannot be in the future."
                    else:
                        data[field_name] = parsed
        elif field_name == "address":
            if value is None or (isinstance(value, str) and not value.strip()):
                data[field_name] = None
            elif not isinstance(value, str) or len(value.strip()) > 2_000:
                errors[field_name] = "Address cannot exceed 2000 characters."
            else:
                data[field_name] = value.strip()
        else:
            max_length = {
                "gender": 50,
                "nationality": 100,
                "marital_status": 50,
                "manager_name": 160,
                "company": 160,
                "location": 160,
                "pan_no": 32,
                "uan_no": 32,
                "bank_account_no": 64,
                "bank_name": 160,
                "ifsc_code": 32,
                "profile_image_path": 500,
            }[field_name]
            if value is None or (isinstance(value, str) and not value.strip()):
                data[field_name] = None
            elif not isinstance(value, str) or len(value.strip()) > max_length:
                errors[field_name] = f"{field_name.replace('_', ' ').title()} cannot exceed {max_length} characters."
            else:
                data[field_name] = value.strip()

    return data, errors
