from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.models import Employee, SalaryStructure

MONEY = Decimal("0.01")
STANDARD_ALLOWANCE = Decimal("4167.00")
PROFESSIONAL_TAX = Decimal("200.00")


def money(value):
    return Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_salary(monthly_wage):
    try:
        wage = money(monthly_wage)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Monthly wage must be a valid amount") from exc
    if wage <= 0:
        raise ValueError("Monthly wage must be positive")

    basic = money(wage * Decimal("0.50"))
    hra = money(basic * Decimal("0.50"))
    performance_bonus = money(basic * Decimal("0.0833"))
    lta = money(basic * Decimal("0.0833"))
    fixed_allowance = money(wage - basic - hra - STANDARD_ALLOWANCE - performance_bonus - lta)
    if fixed_allowance < 0:
        raise ValueError("Monthly wage is too low for the configured components")

    return {
        "monthly_wage": wage,
        "basic_amount": basic,
        "hra_amount": hra,
        "standard_allowance": STANDARD_ALLOWANCE,
        "performance_bonus": performance_bonus,
        "lta_amount": lta,
        "fixed_allowance": fixed_allowance,
        "employee_pf": money(basic * Decimal("0.12")),
        "employer_pf": money(basic * Decimal("0.12")),
        "professional_tax": PROFESSIONAL_TAX,
    }


def save_salary(employee_id, updated_by_user_id, monthly_wage):
    try:
        employee = db.session.get(Employee, employee_id)
        if employee is None:
            raise LookupError("Employee not found")
        values = calculate_salary(monthly_wage)
        salary = employee.salary or SalaryStructure(employee_id=employee_id)
        for field, value in values.items():
            setattr(salary, field, value)
        salary.updated_by_user_id = updated_by_user_id
        db.session.add(salary)
        db.session.commit()
        return salary
    except (LookupError, ValueError, TypeError):
        db.session.rollback()
        raise
    except SQLAlchemyError:
        db.session.rollback()
        raise
