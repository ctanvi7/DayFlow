"""Login identity and one-time temporary password generation."""

from datetime import date
import re
import secrets
import string

from flask import current_app
from sqlalchemy import select

from app.extensions import db
from app.models.user import User


def _name_segment(value: str) -> str:
    letters = "".join(character for character in value if character.isalpha()).upper()
    return letters[:2].ljust(2, "X")


def generate_login_id(first_name: str, last_name: str, joining_date: date) -> str:
    """Generate the next unique annual employee login ID inside the active transaction."""
    company_code = "".join(
        character for character in current_app.config["COMPANY_CODE"] if character.isalnum()
    ).upper()
    if not company_code:
        raise ValueError("COMPANY_CODE must contain at least one alphanumeric character.")

    year = joining_date.year
    prefix = f"{company_code}{_name_segment(first_name)}{_name_segment(last_name)}{year}"
    pattern = re.compile(rf"^{re.escape(company_code)}[A-Z]{{4}}{year}(\d{{4}})$")
    statement = select(User.login_id).where(User.login_id.like(f"{company_code}%{year}%")).with_for_update()
    annual_ids = db.session.scalars(statement).all()
    sequence = max(
        (int(match.group(1)) for login_id in annual_ids if (match := pattern.fullmatch(login_id))),
        default=0,
    ) + 1
    if sequence > 9999:
        raise ValueError("Annual employee login ID sequence has been exhausted.")
    return f"{prefix}{sequence:04d}"


def generate_temporary_password(length: int = 16) -> str:
    """Generate a high-entropy password that meets the Dayflow password policy."""
    if length < 8:
        raise ValueError("Temporary password length must be at least 8 characters.")

    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*_-+=?"),
    ]
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*_-+=?"
    characters = required + [secrets.choice(alphabet) for _ in range(length - len(required))]
    secrets.SystemRandom().shuffle(characters)
    return "".join(characters)
