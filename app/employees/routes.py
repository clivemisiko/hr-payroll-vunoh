from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.employees import bp
from app.models import Employee, Department, User
from app import db


def manager_or_admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_manager:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@bp.route('/')
@login_required
def list_employees():
    """List all active employees (+ deactivated if admin)."""
    show_inactive = request.args.get('inactive', '0') == '1'
    query = Employee.query
    if not show_inactive or not current_user.is_admin:
        query = query.filter_by(is_active=True)
    employees = query.order_by(Employee.first_name).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template(
        'employees/list.html',
        title='Employees',
        employees=employees,
        departments=departments,
        show_inactive=show_inactive,
    )


@bp.route('/org')
@login_required
def org_chart():
    """Org chart view."""
    top_level = Employee.query.filter_by(manager_id=None, is_active=True).all()
    return render_template('employees/org_chart.html', title='Org Chart', top_level=top_level)


@bp.route('/<int:id>')
@login_required
def employee_detail(id):
    employee = Employee.query.get_or_404(id)
    # Employees can only see their own profile unless manager/admin
    if not current_user.is_manager and current_user.employee_id != id:
        abort(403)
    leave_history = sorted(employee.leave_requests, key=lambda r: r.created_at, reverse=True)
    payslips = sorted(employee.payslips, key=lambda p: (p.period.year, p.period.month), reverse=True)
    return render_template(
        'employees/detail.html',
        title=employee.full_name,
        employee=employee,
        leave_history=leave_history,
        payslips=payslips,
    )


@bp.route('/add', methods=['GET', 'POST'])
@login_required
@manager_or_admin_required
def add_employee():
    departments = Department.query.order_by(Department.name).all()
    managers = Employee.query.filter_by(is_active=True).order_by(Employee.first_name).all()

    if request.method == 'POST':
        try:
            emp = Employee(
                first_name=request.form['first_name'].strip(),
                last_name=request.form['last_name'].strip(),
                email=request.form['email'].strip().lower(),
                phone=request.form.get('phone', '').strip(),
                role=request.form['role'].strip(),
                department_id=int(request.form['department_id']) if request.form.get('department_id') else None,
                manager_id=int(request.form['manager_id']) if request.form.get('manager_id') else None,
                start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                salary=float(request.form['salary']),
                employment_type=request.form['employment_type'],
            )
            db.session.add(emp)
            db.session.flush()

            # Create a user account
            password = request.form.get('password', '').strip()
            if password:
                username = f"{emp.first_name.lower()}.{emp.last_name.lower()}"
                # Ensure unique username
                base = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base}{counter}"
                    counter += 1
                u = User(username=username, email=emp.email, role='employee', employee_id=emp.id)
                u.set_password(password)
                db.session.add(u)

            db.session.commit()
            flash(f'Employee {emp.full_name} added successfully.', 'success')
            return redirect(url_for('employees.employee_detail', id=emp.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding employee: {str(e)}', 'danger')

    return render_template(
        'employees/form.html',
        title='Add Employee',
        departments=departments,
        managers=managers,
        employee=None,
    )


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@manager_or_admin_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    departments = Department.query.order_by(Department.name).all()
    managers = Employee.query.filter(
        Employee.is_active == True, Employee.id != id
    ).order_by(Employee.first_name).all()

    if request.method == 'POST':
        try:
            employee.first_name = request.form['first_name'].strip()
            employee.last_name = request.form['last_name'].strip()
            employee.email = request.form['email'].strip().lower()
            employee.phone = request.form.get('phone', '').strip()
            employee.role = request.form['role'].strip()
            employee.department_id = int(request.form['department_id']) if request.form.get('department_id') else None
            employee.manager_id = int(request.form['manager_id']) if request.form.get('manager_id') else None
            employee.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            employee.salary = float(request.form['salary'])
            employee.employment_type = request.form['employment_type']
            db.session.commit()
            flash(f'{employee.full_name} updated successfully.', 'success')
            return redirect(url_for('employees.employee_detail', id=employee.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {str(e)}', 'danger')

    return render_template(
        'employees/form.html',
        title=f'Edit {employee.full_name}',
        departments=departments,
        managers=managers,
        employee=employee,
    )


@bp.route('/<int:id>/deactivate', methods=['POST'])
@login_required
@manager_or_admin_required
def deactivate_employee(id):
    employee = Employee.query.get_or_404(id)
    if not employee.is_active:
        flash('Employee is already inactive.', 'warning')
    else:
        employee.deactivate()
        db.session.commit()
        flash(f'{employee.full_name} has been deactivated. Payroll history is preserved.', 'success')
    return redirect(url_for('employees.list_employees'))


@bp.route('/<int:id>/reactivate', methods=['POST'])
@login_required
@manager_or_admin_required
def reactivate_employee(id):
    employee = Employee.query.get_or_404(id)
    employee.is_active = True
    employee.deactivated_at = None
    db.session.commit()
    flash(f'{employee.full_name} has been reactivated.', 'success')
    return redirect(url_for('employees.employee_detail', id=id))
