"""Authentication and authorization user model."""

from enum import Enum

from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

PRIMARY_KEY_TYPE = db.BigInteger().with_variant(db.Integer, "sqlite")


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    HR = "HR"
    EMPLOYEE = "EMPLOYEE"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(PRIMARY_KEY_TYPE, primary_key=True)
    login_id = db.Column(db.String(24), unique=True, index=True, nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda roles: [role.value for role in roles],
        ),
        nullable=False,
        default=UserRole.EMPLOYEE,
    )
    must_change_password = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    employee = db.relationship("Employee", back_populates="user", uselist=False)

    @validates("login_id")
    def normalize_login_id(self, _key: str, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("Login ID is required.")
        if len(normalized) > 24:
            raise ValueError("Login ID cannot exceed 24 characters.")
        return normalized

    @validates("email")
    def normalize_email(self, _key: str, value: str) -> str:
        normalized = (value or "").strip().lower()
        if not normalized:
            raise ValueError("Email is required.")
        if len(normalized) > 255:
            raise ValueError("Email cannot exceed 255 characters.")
        return normalized

    def set_password(self, password: str) -> None:
        """Hash a password before persisting it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a candidate password without exposing its hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Return fields safe to expose to an authenticated client."""
        return {
            "id": self.id,
            "login_id": self.login_id,
            "email": self.email,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "must_change_password": self.must_change_password,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
