import calendar
from datetime import date, datetime
from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from app.payroll import bp
from app.models import Employee, PayrollPeriod, Payslip
from app.utils.payroll_engine import calculate_payslip
from app.utils.leave_engine import get_unpaid_leave_days
from app import db


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_manager:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@bp.route('/')
@login_required
def list_periods():
    """List all payroll periods."""
    periods = PayrollPeriod.query.order_by(
        PayrollPeriod.year.desc(), PayrollPeriod.month.desc()
    ).all()
    return render_template('payroll/list.html', title='Payroll', periods=periods)


@bp.route('/generate', methods=['GET', 'POST'])
@login_required
@admin_required
def generate():
    """Generate payroll for a period."""
    if request.method == 'POST':
        try:
            year = int(request.form['year'])
            month = int(request.form['month'])

            # Check if already generated
            existing = PayrollPeriod.query.filter_by(year=year, month=month).first()
            if existing and existing.status == 'finalized':
                flash(f'Payroll for {existing.label} is already finalized and cannot be regenerated.', 'danger')
                return redirect(url_for('payroll.list_periods'))

            if not existing:
                period = PayrollPeriod(year=year, month=month, status='draft')
                db.session.add(period)
                db.session.flush()
            else:
                period = existing
                # Delete existing payslips to regenerate
                Payslip.query.filter_by(period_id=period.id).delete()

            # Generate payslips for all ACTIVE employees
            active_employees = Employee.query.filter_by(is_active=True).all()
            generated_count = 0

            for emp in active_employees:
                # Skip employees who joined after this period
                period_last_day = date(year, month, calendar.monthrange(year, month)[1])
                if emp.start_date > period_last_day:
                    continue

                unpaid_days = get_unpaid_leave_days(emp.id, year, month)
                calc = calculate_payslip(emp, year, month, unpaid_days)

                payslip = Payslip(
                    employee_id=emp.id,
                    period_id=period.id,
                    **calc,
                )
                db.session.add(payslip)
                generated_count += 1

            period.status = 'generated'
            period.generated_at = datetime.utcnow()
            period.generated_by = current_user.id
            db.session.commit()

            flash(
                f'Payroll generated for {period.label}: {generated_count} payslips created.',
                'success'
            )
            return redirect(url_for('payroll.period_detail', id=period.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error generating payroll: {str(e)}', 'danger')

    # GET — show form with current/recent months
    today = date.today()
    months = [(today.year, today.month)]
    # Add last 3 months as options
    for i in range(1, 4):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    return render_template(
        'payroll/generate.html',
        title='Generate Payroll',
        months=months,
        calendar=calendar,
    )


@bp.route('/period/<int:id>')
@login_required
def period_detail(id):
    period = PayrollPeriod.query.get_or_404(id)
    if not current_user.is_manager:
        abort(403)
    payslips = Payslip.query.filter_by(period_id=id).join(Employee).order_by(
        Employee.first_name
    ).all()
    total_gross = sum(p.prorated_gross for p in payslips)
    total_net = sum(p.net_pay for p in payslips)
    total_tax = sum(p.income_tax for p in payslips)
    total_ss = sum(p.social_security for p in payslips)

    return render_template(
        'payroll/period_detail.html',
        title=f'Payroll — {period.label}',
        period=period,
        payslips=payslips,
        total_gross=total_gross,
        total_net=total_net,
        total_tax=total_tax,
        total_ss=total_ss,
    )


@bp.route('/period/<int:id>/finalize', methods=['POST'])
@login_required
@admin_required
def finalize_period(id):
    period = PayrollPeriod.query.get_or_404(id)
    if period.status == 'finalized':
        flash('Period is already finalized.', 'warning')
    else:
        period.status = 'finalized'
        db.session.commit()
        flash(f'Payroll for {period.label} has been finalized.', 'success')
    return redirect(url_for('payroll.period_detail', id=id))


@bp.route('/payslip/<int:id>')
@login_required
def payslip_detail(id):
    payslip = Payslip.query.get_or_404(id)
    # Employees can only view their own payslips
    if not current_user.is_manager and current_user.employee_id != payslip.employee_id:
        abort(403)
    return render_template(
        'payroll/payslip.html',
        title=f'Payslip — {payslip.period.label}',
        payslip=payslip,
    )


@bp.route('/my-payslips')
@login_required
def my_payslips():
    if not current_user.employee_id:
        flash('No employee record linked to your account.', 'warning')
        return redirect(url_for('main.dashboard'))
    payslips = Payslip.query.filter_by(
        employee_id=current_user.employee_id
    ).join(PayrollPeriod).order_by(
        PayrollPeriod.year.desc(), PayrollPeriod.month.desc()
    ).all()
    return render_template('payroll/my_payslips.html', title='My Payslips', payslips=payslips)
