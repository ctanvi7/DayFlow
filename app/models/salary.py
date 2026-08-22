from datetime import datetime
from decimal import Decimal

from app.extensions import db


class SalaryStructure(db.Model):
    __tablename__ = "salary_structures"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), unique=True, nullable=False)
    monthly_wage = db.Column(db.Numeric(12, 2), nullable=False)
    basic_amount = db.Column(db.Numeric(12, 2), nullable=False)
    hra_amount = db.Column(db.Numeric(12, 2), nullable=False)
    standard_allowance = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("4167.00"))
    performance_bonus = db.Column(db.Numeric(12, 2), nullable=False)
    lta_amount = db.Column(db.Numeric(12, 2), nullable=False)
    fixed_allowance = db.Column(db.Numeric(12, 2), nullable=False)
    employee_pf = db.Column(db.Numeric(12, 2), nullable=False)
    employer_pf = db.Column(db.Numeric(12, 2), nullable=False)
    professional_tax = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("200.00"))
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    employee = db.relationship("Employee", back_populates="salary")
    updated_by = db.relationship("User", foreign_keys=[updated_by_user_id])
