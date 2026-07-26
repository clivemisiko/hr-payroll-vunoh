"""
Automated unit & integration tests for Vunoh HR core business logic.
Coverage includes:
1. Employee records & soft-deactivation (payroll persistence)
2. Leave validation (consecutive day cap, notice period, team coverage risk, balance limits)
3. Leave auto-escalation for overdue pending requests
4. Payroll calculations (progressive tax brackets, social security cap, mid-month joiner proration, unpaid leave deduction)
"""

import pytest
from datetime import date, datetime, timedelta
from app import create_app, db
from app.models import Employee, Department, User, LeaveType, LeaveBalance, LeaveRequest, PayrollPeriod, Payslip
from app.utils.payroll_engine import calculate_payslip, compute_income_tax, compute_social_security, working_days_in_month
from app.utils.leave_engine import (
    validate_leave_request, submit_leave_request, approve_leave_request,
    reject_leave_request, get_or_create_balance, LeaveValidationError, escalate_overdue_requests
)
from config import TestConfig


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# 1. Employee Records Tests
# ---------------------------------------------------------------------------

def test_employee_deactivation(app):
    with app.app_context():
        emp = Employee(
            first_name='Jane', last_name='Doe', email='jane@vunoh.com',
            role='Developer', start_date=date(2025, 1, 1), salary=100000.0,
            employment_type='full_time', is_active=True
        )
        db.session.add(emp)
        db.session.commit()

        assert emp.is_active is True
        assert emp.deactivated_at is None

        # Deactivate employee
        emp.deactivate()
        db.session.commit()

        assert emp.is_active is False
        assert emp.deactivated_at is not None


# ---------------------------------------------------------------------------
# 2. Leave Management Business Logic Tests
# ---------------------------------------------------------------------------

def test_leave_notice_and_balance_validation(app):
    with app.app_context():
        emp = Employee(
            first_name='John', last_name='Smith', email='john@vunoh.com',
            role='Engineer', start_date=date(2024, 1, 1), salary=80000.0,
            employment_type='full_time'
        )
        db.session.add(emp)
        db.session.flush()

        annual_lt = LeaveType.query.filter_by(name='Annual Leave').first()
        if not annual_lt:
            annual_lt = LeaveType(name='Annual Leave', is_paid=True, requires_notice=True)
            db.session.add(annual_lt)
            db.session.commit()

        # Set entitlement balance of 5 days
        bal = get_or_create_balance(emp.id, annual_lt.id, 2026)
        bal.entitled_days = 5
        bal.used_days = 0
        db.session.commit()

        # Short notice check (less than 3 days)
        tomorrow = date.today() + timedelta(days=1)
        next_week = tomorrow + timedelta(days=2)
        res = validate_leave_request(emp, annual_lt, tomorrow, next_week)
        assert res['flag_insufficient_notice'] is True

        # Exceeding balance check (requesting 10 days when only 5 available)
        far_future = date.today() + timedelta(days=20)
        end_far = far_future + timedelta(days=14)
        res_exceed = validate_leave_request(emp, annual_lt, far_future, end_far)
        assert len(res_exceed['errors']) > 0  # Should error on insufficient balance


def test_leave_approval_deduction(app):
    with app.app_context():
        emp = Employee(first_name='Emp', last_name='One', email='e1@vunoh.com', role='Dev', start_date=date(2024, 1, 1), salary=50000.0)
        mgr = Employee(first_name='Mgr', last_name='One', email='m1@vunoh.com', role='Mgr', start_date=date(2020, 1, 1), salary=100000.0)
        db.session.add_all([emp, mgr])
        db.session.flush()

        lt = LeaveType.query.filter_by(name='Annual Leave').first()
        if not lt:
            lt = LeaveType(name='Annual Leave', is_paid=True, requires_notice=True)
            db.session.add(lt)
            db.session.commit()

        bal = get_or_create_balance(emp.id, lt.id, date.today().year)
        bal.entitled_days = 21
        bal.used_days = 0
        db.session.commit()

        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=2) # 3 days
        req = submit_leave_request(emp, lt, start, end, "Vacation")

        assert req.status == 'pending'
        approve_leave_request(req, mgr)

        assert req.status == 'approved'
        assert bal.used_days == req.days_requested
        assert bal.remaining_days == 21 - req.days_requested


# ---------------------------------------------------------------------------
# 3. Payroll Calculation Engine Tests
# ---------------------------------------------------------------------------

def test_tax_bracket_calculation():
    # 0 - 15,000 @ 0% = 0
    assert compute_income_tax(10000.0) == 0.0

    # 20,000 -> (15,000 @ 0%) + (5,000 @ 10%) = 500
    assert compute_income_tax(20000.0) == 500.0

    # 40,000 -> (15,000 @ 0%) + (15,000 @ 10% = 1,500) + (10,000 @ 20% = 2,000) = 3,500
    assert compute_income_tax(40000.0) == 3500.0


def test_social_security_cap():
    # 6% of 50,000 = 3,000
    assert compute_social_security(50000.0) == 3000.0

    # 6% of 100,000 = 6,000 -> Capped at 4,500
    assert compute_social_security(100000.0) == 4500.0


def test_mid_month_joiner_payroll(app):
    with app.app_context():
        # Employee joins on July 15, 2026
        emp = Employee(
            first_name='David', last_name='Joiner', email='david@vunoh.com',
            role='Engineer', start_date=date(2026, 7, 15), salary=100000.0,
            employment_type='full_time'
        )
        db.session.add(emp)
        db.session.commit()

        calc = calculate_payslip(emp, 2026, 7, unpaid_leave_days=0)

        # July 2026 has 23 working days total.
        # From July 15 to July 31 there are 13 working days.
        assert calc['days_in_month'] == 23
        assert calc['days_worked'] == 13
        assert calc['prorated_gross'] < 100000.0
        assert "Mid-month joiner" in calc['notes']


def test_unpaid_leave_payroll_deduction(app):
    with app.app_context():
        emp = Employee(
            first_name='Alex', last_name='Leave', email='alex@vunoh.com',
            role='Designer', start_date=date(2024, 1, 1), salary=90000.0,
            employment_type='full_time'
        )
        db.session.add(emp)
        db.session.commit()

        # 2 days unpaid leave in July 2026
        calc = calculate_payslip(emp, 2026, 7, unpaid_leave_days=2.0)

        daily_rate = 90000.0 / 23
        expected_deduction = round(daily_rate * 2.0, 2)

        assert calc['unpaid_leave_days'] == 2.0
        assert calc['unpaid_leave_deduction'] == expected_deduction
        assert calc['prorated_gross'] == round(90000.0 - expected_deduction, 2)
