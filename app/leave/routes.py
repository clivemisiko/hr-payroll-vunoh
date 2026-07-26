from datetime import datetime, date
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.leave import bp
from app.models import Employee, LeaveRequest, LeaveType, LeaveBalance
from app.utils.leave_engine import (
    submit_leave_request, approve_leave_request, reject_leave_request,
    LeaveValidationError, validate_leave_request, get_or_create_balance,
    get_employees_on_leave, escalate_overdue_requests,
)
from app import db


@bp.route('/')
@login_required
def list_requests():
    """Leave requests — scoped by role."""
    escalate_overdue_requests()
    status_filter = request.args.get('status', 'all')

    if current_user.is_admin:
        query = LeaveRequest.query
    elif current_user.is_manager and current_user.employee_id:
        team_ids = [
            e.id for e in Employee.query.filter_by(
                manager_id=current_user.employee_id
            ).all()
        ] + [current_user.employee_id]
        query = LeaveRequest.query.filter(LeaveRequest.employee_id.in_(team_ids))
    else:
        query = LeaveRequest.query.filter_by(employee_id=current_user.employee_id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    requests_list = query.order_by(LeaveRequest.created_at.desc()).all()
    leave_types = LeaveType.query.all()

    return render_template(
        'leave/list.html',
        title='Leave Requests',
        leave_requests=requests_list,
        leave_types=leave_types,
        status_filter=status_filter,
    )


@bp.route('/calendar')
@login_required
def calendar():
    """Who's out calendar view."""
    on_leave_today = get_employees_on_leave(date.today())
    upcoming = LeaveRequest.query.filter(
        LeaveRequest.status == 'approved',
        LeaveRequest.end_date >= date.today(),
    ).order_by(LeaveRequest.start_date).limit(30).all()
    return render_template(
        'leave/calendar.html',
        title="Who's Out",
        on_leave_today=on_leave_today,
        upcoming=upcoming,
        today=date.today(),
    )


@bp.route('/request', methods=['GET', 'POST'])
@login_required
def request_leave():
    """Submit a new leave request."""
    if not current_user.employee_id:
        flash('Your account is not linked to an employee record.', 'danger')
        return redirect(url_for('main.dashboard'))

    employee = Employee.query.get(current_user.employee_id)
    leave_types = LeaveType.query.all()

    validation_result = None
    warnings = []

    if request.method == 'POST':
        action = request.form.get('action', 'submit')
        try:
            lt_id = int(request.form['leave_type_id'])
            leave_type = LeaveType.query.get_or_404(lt_id)
            start = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            reason = request.form.get('reason', '').strip()

            if action == 'preview':
                validation_result = validate_leave_request(employee, leave_type, start, end)
                warnings = validation_result.get('warnings', [])
                return render_template(
                    'leave/request_form.html',
                    title='Request Leave',
                    employee=employee,
                    leave_types=leave_types,
                    validation_result=validation_result,
                    warnings=warnings,
                    form_data=request.form,
                )

            lr = submit_leave_request(employee, leave_type, start, end, reason)
            flash(f'Leave request submitted successfully (#{lr.id}).', 'success')
            if lr.flag_insufficient_notice:
                flash('⚠ Flagged: Insufficient notice period. Manager review required.', 'warning')
            if lr.flag_team_coverage_risk:
                flash('⚠ Flagged: Team coverage risk. Manager review required.', 'warning')
            return redirect(url_for('leave.list_requests'))

        except LeaveValidationError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Error submitting request: {str(e)}', 'danger')

    # Pre-populate balances
    year = date.today().year
    balances = {}
    for lt in leave_types:
        bal = get_or_create_balance(employee.id, lt.id, year)
        balances[lt.id] = bal

    return render_template(
        'leave/request_form.html',
        title='Request Leave',
        employee=employee,
        leave_types=leave_types,
        balances=balances,
        validation_result=None,
        warnings=[],
        form_data={},
    )


@bp.route('/<int:id>')
@login_required
def view_request(id):
    lr = LeaveRequest.query.get_or_404(id)
    # Access control
    if not current_user.is_manager and current_user.employee_id != lr.employee_id:
        abort(403)
    return render_template('leave/detail.html', title=f'Leave Request #{id}', lr=lr)


@bp.route('/<int:id>/approve', methods=['POST'])
@login_required
def approve(id):
    if not current_user.is_manager:
        abort(403)
    lr = LeaveRequest.query.get_or_404(id)
    reviewer = Employee.query.get(current_user.employee_id)
    if not reviewer and current_user.is_admin:
        # Admin without employee record — use a placeholder
        reviewer = Employee.query.first()
    try:
        approve_leave_request(lr, reviewer)
        flash(f'Leave request #{id} approved.', 'success')
    except LeaveValidationError as e:
        flash(str(e), 'danger')
    return redirect(request.referrer or url_for('leave.list_requests'))


@bp.route('/<int:id>/reject', methods=['POST'])
@login_required
def reject(id):
    if not current_user.is_manager:
        abort(403)
    lr = LeaveRequest.query.get_or_404(id)
    reviewer = Employee.query.get(current_user.employee_id)
    if not reviewer and current_user.is_admin:
        reviewer = Employee.query.first()
    reason = request.form.get('rejection_reason', '').strip()
    try:
        reject_leave_request(lr, reviewer, reason)
        flash(f'Leave request #{id} rejected.', 'info')
    except LeaveValidationError as e:
        flash(str(e), 'danger')
    return redirect(request.referrer or url_for('leave.list_requests'))


@bp.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel(id):
    lr = LeaveRequest.query.get_or_404(id)
    if current_user.employee_id != lr.employee_id and not current_user.is_manager:
        abort(403)
    if lr.status not in ('pending',):
        flash('Only pending requests can be cancelled.', 'warning')
    else:
        lr.status = 'cancelled'
        db.session.commit()
        flash('Leave request cancelled.', 'info')
    return redirect(url_for('leave.list_requests'))


@bp.route('/balances')
@login_required
def balances():
    """View leave balances."""
    year = int(request.args.get('year', date.today().year))
    employee_id = request.args.get('employee_id', current_user.employee_id)

    if not current_user.is_manager:
        employee_id = current_user.employee_id

    if not employee_id:
        flash('No employee record linked.', 'warning')
        return redirect(url_for('main.dashboard'))

    employee = Employee.query.get_or_404(employee_id)
    leave_types = LeaveType.query.all()
    balances_data = []
    for lt in leave_types:
        bal = get_or_create_balance(employee.id, lt.id, year)
        balances_data.append({
            'leave_type': lt,
            'balance': bal,
        })

    all_employees = Employee.query.filter_by(is_active=True).all() if current_user.is_manager else []

    return render_template(
        'leave/balances.html',
        title='Leave Balances',
        employee=employee,
        balances_data=balances_data,
        year=year,
        all_employees=all_employees,
    )
