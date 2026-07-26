from datetime import date
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.main import bp
from app.models import Employee, LeaveRequest, PayrollPeriod
from app.utils.leave_engine import get_employees_on_leave, escalate_overdue_requests


@bp.route('/')
def index():
    """Public landing page."""
    return render_template('main/index.html', title='Vunoh Global HR')


@bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard — different views for admin/manager/employee."""
    escalate_overdue_requests()

    # Stats for admin/manager
    total_employees = Employee.query.filter_by(is_active=True).count()
    on_leave_today = get_employees_on_leave(date.today())
    pending_requests = LeaveRequest.query.filter_by(status='pending').count()
    escalated_requests = LeaveRequest.query.filter_by(status='escalated').count()

    # Pending approvals for managers
    pending_leave = []
    if current_user.is_manager and current_user.employee_id:
        # Employees whose manager is current user
        my_team_ids = [
            e.id for e in Employee.query.filter_by(
                manager_id=current_user.employee_id, is_active=True
            ).all()
        ]
        pending_leave = LeaveRequest.query.filter(
            LeaveRequest.employee_id.in_(my_team_ids),
            LeaveRequest.status.in_(['pending', 'escalated']),
        ).order_by(LeaveRequest.created_at.asc()).all()

    if current_user.is_admin:
        pending_leave = LeaveRequest.query.filter(
            LeaveRequest.status.in_(['pending', 'escalated'])
        ).order_by(LeaveRequest.created_at.asc()).all()

    # Recent payroll period
    latest_period = PayrollPeriod.query.order_by(
        PayrollPeriod.year.desc(), PayrollPeriod.month.desc()
    ).first()

    # Employee's own upcoming leaves
    my_upcoming_leaves = []
    if current_user.employee_id:
        my_upcoming_leaves = LeaveRequest.query.filter(
            LeaveRequest.employee_id == current_user.employee_id,
            LeaveRequest.status == 'approved',
            LeaveRequest.end_date >= date.today(),
        ).order_by(LeaveRequest.start_date.asc()).limit(3).all()

    return render_template(
        'main/dashboard.html',
        title='Dashboard',
        total_employees=total_employees,
        on_leave_today=on_leave_today,
        pending_requests=pending_requests,
        escalated_requests=escalated_requests,
        pending_leave=pending_leave,
        latest_period=latest_period,
        my_upcoming_leaves=my_upcoming_leaves,
        today=date.today(),
    )
