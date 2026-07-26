"""
Leave business logic — validation rules, balance management, escalation.

Problems identified in spreadsheet-based leave management:
1. Under-coverage: A whole team requests leave on the same dates
2. Requests sitting unanswered: No escalation or reminders
3. Insufficient notice: Last-minute requests (except emergencies)
4. Balance exceeded: Requesting more days than entitled
5. Consecutive day cap: Extremely long leaves going unchecked
6. Unpaid leave not linked to payroll: Manual recalculation errors

Solutions implemented:
- Team coverage check: reject/warn if < MIN_TEAM_COVERAGE active
- Auto-escalation: flag requests older than ESCALATION_DAYS
- Notice period: warn/block non-emergency requests < MIN_NOTICE_DAYS ahead
- Balance validation: hard-block if no remaining days
- Max consecutive cap: block requests > MAX_CONSECUTIVE_DAYS
- Leave ↔ Payroll link: approved unpaid leave auto-feeds payroll engine
"""

from datetime import date, datetime, timedelta
from flask import current_app
from app import db
from app.models import Employee, LeaveBalance, LeaveRequest, LeaveType


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class LeaveValidationError(Exception):
    """Raised when leave request fails a hard business rule."""
    pass


def count_working_days(start: date, end: date) -> int:
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


def get_or_create_balance(employee_id: int, leave_type_id: int, year: int) -> LeaveBalance:
    """Fetch or initialise a leave balance record for the year."""
    balance = LeaveBalance.query.filter_by(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        year=year,
    ).first()

    if not balance:
        from flask import current_app
        employee = Employee.query.get(employee_id)
        leave_type = LeaveType.query.get(leave_type_id)

        if leave_type.max_days_per_year is not None:
            entitled = leave_type.max_days_per_year
        else:
            entitled = current_app.config['ANNUAL_LEAVE_DAYS'].get(
                employee.employment_type, 21
            )

        balance = LeaveBalance(
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            year=year,
            entitled_days=entitled,
            used_days=0,
            carried_over=0,
        )
        db.session.add(balance)
        db.session.commit()

    return balance


def validate_leave_request(
    employee: Employee,
    leave_type: LeaveType,
    start_date: date,
    end_date: date,
) -> dict:
    """
    Run all business rule checks. Returns a dict with:
      - 'errors': list of hard-block messages (request must be rejected)
      - 'warnings': list of flags (informational, manager can override)
      - flags: individual boolean flags for DB storage
    """
    errors = []
    warnings = []
    flags = {
        'flag_insufficient_notice': False,
        'flag_team_coverage_risk': False,
        'flag_balance_exceeded': False,
    }
    cfg = current_app.config

    days_requested = count_working_days(start_date, end_date)

    # 1. Date sanity
    if end_date < start_date:
        errors.append("End date cannot be before start date.")
    if start_date < date.today():
        errors.append("Cannot request leave for a date in the past.")

    # 2. Consecutive day cap (hard block)
    max_consec = cfg['LEAVE_MAX_CONSECUTIVE_DAYS']
    if days_requested > max_consec:
        errors.append(
            f"Single leave request cannot exceed {max_consec} working days. "
            f"Split into multiple requests."
        )

    # 3. Notice period (soft flag for non-emergency types)
    if leave_type.requires_notice:
        notice_days = (start_date - date.today()).days
        min_notice = cfg['LEAVE_MIN_NOTICE_DAYS']
        if notice_days < min_notice:
            flags['flag_insufficient_notice'] = True
            warnings.append(
                f"Insufficient notice: {notice_days} day(s) given, {min_notice} required. "
                f"Manager approval still possible."
            )

    # 4. Leave balance check
    balance = get_or_create_balance(employee.id, leave_type.id, start_date.year)
    if balance.remaining_days < days_requested:
        flags['flag_balance_exceeded'] = True
        if leave_type.is_paid:
            errors.append(
                f"Insufficient {leave_type.name} balance. "
                f"Requested: {days_requested} day(s), Available: {balance.remaining_days:.1f} day(s)."
            )
        else:
            warnings.append(
                f"Requested {days_requested} day(s) exceeds remaining {leave_type.name} balance "
                f"({balance.remaining_days:.1f}). Excess will be unpaid."
            )

    # 5. Team coverage check
    if employee.manager_id:
        team = Employee.query.filter(
            Employee.manager_id == employee.manager_id,
            Employee.is_active == True,
            Employee.id != employee.id,
        ).all()

        # Count team members already on approved leave during requested period
        on_leave = 0
        for member in team:
            overlap = LeaveRequest.query.filter(
                LeaveRequest.employee_id == member.id,
                LeaveRequest.status == 'approved',
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
            ).count()
            if overlap:
                on_leave += 1

        total_team = len(team) + 1  # include requestor
        present = total_team - on_leave - 1  # subtract requestor
        min_coverage = cfg['LEAVE_MIN_TEAM_COVERAGE']

        if present < min_coverage:
            flags['flag_team_coverage_risk'] = True
            warnings.append(
                f"Team coverage risk: only {present} team member(s) would remain "
                f"(minimum {min_coverage} required). Manager override needed."
            )

    return {
        'errors': errors,
        'warnings': warnings,
        **flags,
        'days_requested': days_requested,
    }


# ---------------------------------------------------------------------------
# Request lifecycle
# ---------------------------------------------------------------------------

def submit_leave_request(employee: Employee, leave_type: LeaveType,
                          start_date: date, end_date: date, reason: str) -> LeaveRequest:
    """Validate and create a leave request."""
    validation = validate_leave_request(employee, leave_type, start_date, end_date)

    if validation['errors']:
        raise LeaveValidationError('; '.join(validation['errors']))

    request = LeaveRequest(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start_date,
        end_date=end_date,
        days_requested=validation['days_requested'],
        reason=reason,
        status='pending',
        flag_insufficient_notice=validation['flag_insufficient_notice'],
        flag_team_coverage_risk=validation['flag_team_coverage_risk'],
        flag_balance_exceeded=validation['flag_balance_exceeded'],
    )
    db.session.add(request)
    db.session.commit()
    return request


def approve_leave_request(request: LeaveRequest, reviewer: Employee) -> LeaveRequest:
    """Approve a leave request and deduct from balance."""
    if request.status != 'pending':
        raise LeaveValidationError(f"Cannot approve a {request.status} request.")

    balance = get_or_create_balance(
        request.employee_id,
        request.leave_type_id,
        request.start_date.year,
    )
    balance.used_days += request.days_requested
    request.status = 'approved'
    request.reviewed_by = reviewer.id
    request.reviewed_at = datetime.utcnow()
    db.session.commit()
    return request


def reject_leave_request(request: LeaveRequest, reviewer: Employee, reason: str = '') -> LeaveRequest:
    """Reject a leave request."""
    if request.status != 'pending':
        raise LeaveValidationError(f"Cannot reject a {request.status} request.")
    request.status = 'rejected'
    request.reviewed_by = reviewer.id
    request.reviewed_at = datetime.utcnow()
    request.rejection_reason = reason
    db.session.commit()
    return request


def escalate_overdue_requests():
    """
    Mark pending requests that have been waiting > ESCALATION_DAYS as 'escalated'.
    Should be called on a schedule or at page load.
    """
    threshold = current_app.config['LEAVE_ESCALATION_DAYS']
    cutoff = datetime.utcnow() - timedelta(days=threshold)
    overdue = LeaveRequest.query.filter(
        LeaveRequest.status == 'pending',
        LeaveRequest.created_at <= cutoff,
        LeaveRequest.escalated_at == None,
    ).all()
    for req in overdue:
        req.status = 'escalated'
        req.escalated_at = datetime.utcnow()
    if overdue:
        db.session.commit()
    return len(overdue)


def get_employees_on_leave(target_date: date = None):
    """Return list of employees currently on approved leave."""
    if target_date is None:
        target_date = date.today()
    requests = LeaveRequest.query.filter(
        LeaveRequest.status == 'approved',
        LeaveRequest.start_date <= target_date,
        LeaveRequest.end_date >= target_date,
    ).all()
    return [r.employee for r in requests]


def get_unpaid_leave_days(employee_id: int, year: int, month: int) -> float:
    """
    Calculate unpaid leave days for an employee in a specific month.
    Used by the payroll engine.
    """
    from calendar import monthrange
    from datetime import date as dt
    _, last_day = monthrange(year, month)
    period_start = dt(year, month, 1)
    period_end = dt(year, month, last_day)

    unpaid_types = LeaveType.query.filter_by(is_paid=False).all()
    unpaid_type_ids = [lt.id for lt in unpaid_types]

    if not unpaid_type_ids:
        return 0.0

    requests = LeaveRequest.query.filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status == 'approved',
        LeaveRequest.leave_type_id.in_(unpaid_type_ids),
        LeaveRequest.start_date <= period_end,
        LeaveRequest.end_date >= period_start,
    ).all()

    total_unpaid = 0.0
    for req in requests:
        overlap_start = max(req.start_date, period_start)
        overlap_end = min(req.end_date, period_end)
        total_unpaid += count_working_days(overlap_start, overlap_end)

    return total_unpaid
