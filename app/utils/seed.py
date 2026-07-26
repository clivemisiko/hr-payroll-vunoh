"""
Seed the database with sample data on first run.
Creates departments, employees, users, leave types, and sample leave requests.
"""
from datetime import date, datetime, timedelta
from app import db
from app.models import (
    Department, Employee, User, LeaveType, LeaveBalance, LeaveRequest, PayrollPeriod
)


def seed_data():
    """Idempotent seed — only runs if no data exists."""
    if User.query.first():
        return

    # -------- Departments --------
    depts = {
        'Engineering': Department(name='Engineering', description='Software and infrastructure'),
        'Sales': Department(name='Sales', description='Revenue and business development'),
        'HR': Department(name='HR', description='People & culture'),
        'Finance': Department(name='Finance', description='Financial operations'),
        'Operations': Department(name='Operations', description='Day-to-day operations'),
    }
    for d in depts.values():
        db.session.add(d)
    db.session.flush()

    # -------- Leave Types --------
    leave_types = {
        'Annual': LeaveType(name='Annual Leave', is_paid=True, requires_notice=True, description='Standard annual leave'),
        'Sick': LeaveType(name='Sick Leave', is_paid=True, requires_notice=False, max_days_per_year=10, description='Medical illness'),
        'Emergency': LeaveType(name='Emergency Leave', is_paid=True, requires_notice=False, max_days_per_year=5, description='Personal emergency'),
        'Unpaid': LeaveType(name='Unpaid Leave', is_paid=False, requires_notice=True, description='Leave without pay'),
        'Maternity': LeaveType(name='Maternity Leave', is_paid=True, requires_notice=True, max_days_per_year=90, description='Maternity leave'),
        'Study': LeaveType(name='Study Leave', is_paid=False, requires_notice=True, max_days_per_year=10, description='Approved study or exam'),
    }
    for lt in leave_types.values():
        db.session.add(lt)
    db.session.flush()

    # -------- Employees --------
    # CEO / Top-level
    ceo = Employee(
        first_name='James', last_name='Vunoh',
        email='james.vunoh@vunohglobal.com',
        role='Chief Executive Officer',
        department_id=depts['HR'].id,
        manager_id=None,
        start_date=date(2020, 1, 15),
        salary=250_000.0,
        employment_type='full_time',
    )
    db.session.add(ceo)
    db.session.flush()

    # HR Manager
    hr_mgr = Employee(
        first_name='Amina', last_name='Ochieng',
        email='amina.ochieng@vunohglobal.com',
        role='HR Manager',
        department_id=depts['HR'].id,
        manager_id=ceo.id,
        start_date=date(2021, 3, 1),
        salary=120_000.0,
        employment_type='full_time',
    )
    db.session.add(hr_mgr)

    # Engineering Manager
    eng_mgr = Employee(
        first_name='Brian', last_name='Kamau',
        email='brian.kamau@vunohglobal.com',
        role='Engineering Manager',
        department_id=depts['Engineering'].id,
        manager_id=ceo.id,
        start_date=date(2021, 6, 1),
        salary=180_000.0,
        employment_type='full_time',
    )
    db.session.add(eng_mgr)
    db.session.flush()

    # Engineers
    alice = Employee(
        first_name='Alice', last_name='Njeri',
        email='alice.njeri@vunohglobal.com',
        role='Senior Software Engineer',
        department_id=depts['Engineering'].id,
        manager_id=eng_mgr.id,
        start_date=date(2022, 2, 14),
        salary=130_000.0,
        employment_type='full_time',
    )
    bob = Employee(
        first_name='Bob', last_name='Otieno',
        email='bob.otieno@vunohglobal.com',
        role='Software Engineer',
        department_id=depts['Engineering'].id,
        manager_id=eng_mgr.id,
        start_date=date(2023, 5, 1),
        salary=95_000.0,
        employment_type='full_time',
    )
    carol = Employee(
        first_name='Carol', last_name='Wambua',
        email='carol.wambua@vunohglobal.com',
        role='Junior Software Engineer',
        department_id=depts['Engineering'].id,
        manager_id=eng_mgr.id,
        start_date=date(2024, 9, 1),
        salary=65_000.0,
        employment_type='full_time',
    )
    # Mid-month joiner for payroll demo
    david = Employee(
        first_name='David', last_name='Mwangi',
        email='david.mwangi@vunohglobal.com',
        role='DevOps Engineer',
        department_id=depts['Engineering'].id,
        manager_id=eng_mgr.id,
        start_date=date(2026, 7, 15),   # mid-month joiner
        salary=110_000.0,
        employment_type='full_time',
    )
    # Sales
    sales_mgr = Employee(
        first_name='Peter', last_name='Ndungu',
        email='peter.ndungu@vunohglobal.com',
        role='Sales Manager',
        department_id=depts['Sales'].id,
        manager_id=ceo.id,
        start_date=date(2021, 8, 1),
        salary=135_000.0,
        employment_type='full_time',
    )
    sales_rep = Employee(
        first_name='Grace', last_name='Achieng',
        email='grace.achieng@vunohglobal.com',
        role='Sales Representative',
        department_id=depts['Sales'].id,
        manager_id=None,
        start_date=date(2023, 1, 10),
        salary=70_000.0,
        employment_type='full_time',
    )
    db.session.flush()
    sales_rep.manager_id = sales_mgr.id

    # Part-time / contract
    intern = Employee(
        first_name='Felix', last_name='Mugo',
        email='felix.mugo@vunohglobal.com',
        role='Engineering Intern',
        department_id=depts['Engineering'].id,
        manager_id=eng_mgr.id,
        start_date=date(2026, 6, 1),
        salary=25_000.0,
        employment_type='intern',
    )
    # Deactivated employee (payroll history must persist)
    former = Employee(
        first_name='Janet', last_name='Maina',
        email='janet.maina@vunohglobal.com',
        role='QA Engineer',
        department_id=depts['Engineering'].id,
        manager_id=eng_mgr.id,
        start_date=date(2022, 4, 1),
        salary=88_000.0,
        employment_type='full_time',
        is_active=False,
        deactivated_at=datetime(2026, 5, 31),
    )
    for emp in [alice, bob, carol, david, sales_mgr, sales_rep, intern, former]:
        db.session.add(emp)
    db.session.flush()

    # -------- Users --------
    users_data = [
        ('admin', 'admin@vunohglobal.com', 'Admin@1234', 'admin', None),
        ('james.vunoh', 'james.vunoh@vunohglobal.com', 'Vunoh@1234', 'manager', ceo.id),
        ('amina.ochieng', 'amina.ochieng@vunohglobal.com', 'Hr@1234', 'manager', hr_mgr.id),
        ('brian.kamau', 'brian.kamau@vunohglobal.com', 'Eng@1234', 'manager', eng_mgr.id),
        ('alice.njeri', 'alice.njeri@vunohglobal.com', 'Alice@1234', 'employee', alice.id),
        ('bob.otieno', 'bob.otieno@vunohglobal.com', 'Bob@1234', 'employee', bob.id),
        ('carol.wambua', 'carol.wambua@vunohglobal.com', 'Carol@1234', 'employee', carol.id),
        ('peter.ndungu', 'peter.ndungu@vunohglobal.com', 'Sales@1234', 'manager', sales_mgr.id),
        ('grace.achieng', 'grace.achieng@vunohglobal.com', 'Grace@1234', 'employee', sales_rep.id),
        ('felix.mugo', 'felix.mugo@vunohglobal.com', 'Felix@1234', 'employee', intern.id),
    ]
    for username, email, pwd, role, emp_id in users_data:
        u = User(username=username, email=email, role=role, employee_id=emp_id)
        u.set_password(pwd)
        db.session.add(u)
    db.session.flush()

    # -------- Leave Balances & Sample Requests --------
    current_year = date.today().year
    all_employees = [ceo, hr_mgr, eng_mgr, alice, bob, carol, david, sales_mgr, sales_rep, intern]
    for emp in all_employees:
        for lt in [leave_types['Annual'], leave_types['Sick'], leave_types['Emergency']]:
            if lt.max_days_per_year is not None:
                entitled = lt.max_days_per_year
            else:
                from flask import current_app
                entitled = current_app.config['ANNUAL_LEAVE_DAYS'].get(emp.employment_type, 21)
            bal = LeaveBalance(
                employee_id=emp.id,
                leave_type_id=lt.id,
                year=current_year,
                entitled_days=entitled,
                used_days=0,
                carried_over=0,
            )
            db.session.add(bal)
    db.session.flush()

    today = date.today()
    # Approved past leave
    req1 = LeaveRequest(
        employee_id=alice.id,
        leave_type_id=leave_types['Annual'].id,
        start_date=today - timedelta(days=20),
        end_date=today - timedelta(days=16),
        days_requested=5,
        reason='Family vacation',
        status='approved',
        reviewed_by=eng_mgr.id,
        reviewed_at=datetime.utcnow() - timedelta(days=22),
    )
    db.session.add(req1)

    # Update Alice's balance
    alice_annual = LeaveBalance.query.filter_by(
        employee_id=alice.id,
        leave_type_id=leave_types['Annual'].id,
        year=current_year,
    ).first()
    if alice_annual:
        alice_annual.used_days = 5

    # Pending requests (for dashboard demo)
    req2 = LeaveRequest(
        employee_id=bob.id,
        leave_type_id=leave_types['Annual'].id,
        start_date=today + timedelta(days=7),
        end_date=today + timedelta(days=11),
        days_requested=5,
        reason='Personal travel',
        status='pending',
        flag_insufficient_notice=False,
    )
    req3 = LeaveRequest(
        employee_id=carol.id,
        leave_type_id=leave_types['Sick'].id,
        start_date=today - timedelta(days=1),
        end_date=today,
        days_requested=2,
        reason='Flu',
        status='pending',
        flag_insufficient_notice=False,
    )
    # Escalated (old pending)
    req4 = LeaveRequest(
        employee_id=sales_rep.id,
        leave_type_id=leave_types['Annual'].id,
        start_date=today + timedelta(days=14),
        end_date=today + timedelta(days=18),
        days_requested=5,
        reason='Wedding',
        status='escalated',
        escalated_at=datetime.utcnow(),
        created_at=datetime.utcnow() - timedelta(days=5),
    )
    for r in [req2, req3, req4]:
        db.session.add(r)

    # -------- Sample Payroll Period --------
    last_month = today.replace(day=1) - timedelta(days=1)
    period = PayrollPeriod(
        year=last_month.year,
        month=last_month.month,
        status='generated',
        generated_at=datetime.utcnow() - timedelta(days=3),
    )
    db.session.add(period)

    db.session.commit()
    print('[Seed] Database seeded with sample data.')
