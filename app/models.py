"""
Database models for Vunoh HR & Payroll system.
"""
from datetime import datetime, date, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


# ---------------------------------------------------------------------------
# User / Auth
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # admin | manager | employee
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='user', foreign_keys=[employee_id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role in ('admin', 'manager')

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Employee
# ---------------------------------------------------------------------------

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employees = db.relationship('Employee', back_populates='department')

    def __repr__(self):
        return f'<Department {self.name}>'


class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    role = db.Column(db.String(100), nullable=False)                    # Job title / role
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Float, nullable=False)                         # Monthly gross salary
    employment_type = db.Column(db.String(20), nullable=False, default='full_time')
    # full_time | part_time | contract | intern
    is_active = db.Column(db.Boolean, default=True, nullable=False)      # soft-delete
    deactivated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship('Department', back_populates='employees')
    manager = db.relationship('Employee', remote_side=[id], backref='direct_reports', foreign_keys=[manager_id])
    user = db.relationship('User', back_populates='employee', foreign_keys='User.employee_id', uselist=False)
    leave_requests = db.relationship('LeaveRequest', back_populates='employee', foreign_keys='LeaveRequest.employee_id')
    leave_balances = db.relationship('LeaveBalance', back_populates='employee')
    payslips = db.relationship('Payslip', back_populates='employee')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def team_members(self):
        """All employees that share the same manager (including self)."""
        if self.manager_id:
            return Employee.query.filter_by(manager_id=self.manager_id, is_active=True).all()
        return []

    def deactivate(self):
        self.is_active = False
        self.deactivated_at = datetime.utcnow()

    def years_of_service(self):
        delta = date.today() - self.start_date
        return round(delta.days / 365.25, 1)

    def __repr__(self):
        return f'<Employee {self.full_name}>'


# ---------------------------------------------------------------------------
# Leave
# ---------------------------------------------------------------------------

class LeaveType(db.Model):
    __tablename__ = 'leave_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)   # Annual, Sick, Maternity, Emergency, etc.
    is_paid = db.Column(db.Boolean, default=True)
    requires_notice = db.Column(db.Boolean, default=True)          # False for sick/emergency
    max_days_per_year = db.Column(db.Integer, nullable=True)        # None = use global entitlement
    description = db.Column(db.String(255))

    requests = db.relationship('LeaveRequest', back_populates='leave_type')
    balances = db.relationship('LeaveBalance', back_populates='leave_type')

    def __repr__(self):
        return f'<LeaveType {self.name}>'


class LeaveBalance(db.Model):
    __tablename__ = 'leave_balances'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    entitled_days = db.Column(db.Float, nullable=False, default=0)
    used_days = db.Column(db.Float, nullable=False, default=0)
    carried_over = db.Column(db.Float, nullable=False, default=0)

    employee = db.relationship('Employee', back_populates='leave_balances')
    leave_type = db.relationship('LeaveType', back_populates='balances')

    @property
    def remaining_days(self):
        return self.entitled_days + self.carried_over - self.used_days

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'leave_type_id', 'year', name='_emp_lt_year_uc'),
    )

    def __repr__(self):
        return f'<LeaveBalance {self.employee_id} {self.leave_type_id} {self.year}>'


class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='pending')
    # pending | approved | rejected | cancelled | escalated
    reviewed_by = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    escalated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Validation flags (set by business logic)
    flag_insufficient_notice = db.Column(db.Boolean, default=False)
    flag_team_coverage_risk = db.Column(db.Boolean, default=False)
    flag_balance_exceeded = db.Column(db.Boolean, default=False)

    employee = db.relationship('Employee', back_populates='leave_requests', foreign_keys=[employee_id])
    reviewer = db.relationship('Employee', foreign_keys=[reviewed_by])
    leave_type = db.relationship('LeaveType', back_populates='requests')

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_overdue(self):
        """Pending for more than LEAVE_ESCALATION_DAYS."""
        if self.status != 'pending':
            return False
        from flask import current_app
        threshold = current_app.config['LEAVE_ESCALATION_DAYS']
        return (datetime.utcnow() - self.created_at).days >= threshold

    def __repr__(self):
        return f'<LeaveRequest {self.id} {self.employee_id} {self.status}>'


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------

class PayrollPeriod(db.Model):
    __tablename__ = 'payroll_periods'

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)          # 1–12
    status = db.Column(db.String(20), default='draft')     # draft | generated | finalized
    generated_at = db.Column(db.DateTime, nullable=True)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    payslips = db.relationship('Payslip', back_populates='period')

    __table_args__ = (
        db.UniqueConstraint('year', 'month', name='_year_month_uc'),
    )

    @property
    def label(self):
        import calendar
        return f"{calendar.month_name[self.month]} {self.year}"

    def __repr__(self):
        return f'<PayrollPeriod {self.year}-{self.month}>'


class Payslip(db.Model):
    __tablename__ = 'payslips'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    period_id = db.Column(db.Integer, db.ForeignKey('payroll_periods.id'), nullable=False)

    # Earnings
    gross_salary = db.Column(db.Float, nullable=False)        # full monthly salary
    days_in_month = db.Column(db.Integer, nullable=False)
    days_worked = db.Column(db.Float, nullable=False)         # pro-rated for joiners / unpaid leave
    prorated_gross = db.Column(db.Float, nullable=False)      # actual gross after proration

    # Unpaid leave deduction
    unpaid_leave_days = db.Column(db.Float, nullable=False, default=0)
    unpaid_leave_deduction = db.Column(db.Float, nullable=False, default=0)

    # Statutory deductions
    taxable_income = db.Column(db.Float, nullable=False)
    income_tax = db.Column(db.Float, nullable=False)
    social_security = db.Column(db.Float, nullable=False)
    total_deductions = db.Column(db.Float, nullable=False)

    # Net
    net_pay = db.Column(db.Float, nullable=False)

    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship('Employee', back_populates='payslips')
    period = db.relationship('PayrollPeriod', back_populates='payslips')

    __table_args__ = (
        db.UniqueConstraint('employee_id', 'period_id', name='_emp_period_uc'),
    )

    def __repr__(self):
        return f'<Payslip {self.employee_id} {self.period_id}>'
