"""
Payroll calculation engine for Vunoh HR.

Tax Bracket Formula (fictional, documented):
----------------------------------------------
Gross Taxable = Prorated Gross - Social Security

Tax Brackets (monthly taxable income):
  0 – 15,000       → 0%
  15,001 – 30,000  → 10%  on amount above 15,000
  30,001 – 60,000  → 20%  on amount above 30,000 (+ 1,500)
  60,001+          → 30%  on amount above 60,000 (+ 7,500)

Social Security:
  Employee contribution: 6% of gross (capped at 4,500)
  (Employer contribution not modelled — outside payslip scope)

Edge cases handled:
  - Mid-month joiners: pro-rated by working days
  - Unpaid leave: daily rate deducted before tax
  - Zero-deduction: when taxable income ≤ 15,000
  - Boundary brackets: computed precisely at thresholds
"""

import calendar
from datetime import date
from typing import Tuple


SOCIAL_SECURITY_RATE = 0.06       # 6% of gross
SOCIAL_SECURITY_CAP = 4_500.0     # max SS deduction

TAX_BRACKETS = [
    (15_000, 0.00),    # 0% on first 15,000
    (30_000, 0.10),    # 10% on 15,001–30,000
    (60_000, 0.20),    # 20% on 30,001–60,000
    (float('inf'), 0.30),  # 30% above 60,000
]


def compute_social_security(gross: float) -> float:
    """Employee SS contribution (6% of gross, capped at 4,500)."""
    return min(gross * SOCIAL_SECURITY_RATE, SOCIAL_SECURITY_CAP)


def compute_income_tax(taxable_income: float) -> float:
    """
    Progressive tax on taxable income (gross - social security).
    Returns 0 for zero or negative taxable income.
    """
    if taxable_income <= 0:
        return 0.0

    tax = 0.0
    previous_limit = 0.0

    for limit, rate in TAX_BRACKETS:
        if taxable_income <= previous_limit:
            break
        band_income = min(taxable_income, limit) - previous_limit
        tax += band_income * rate
        previous_limit = limit

    return round(tax, 2)


def working_days_in_month(year: int, month: int) -> int:
    """Count Mon–Fri working days in the given month."""
    _, days_in_month = calendar.monthrange(year, month)
    count = 0
    for day in range(1, days_in_month + 1):
        weekday = date(year, month, day).weekday()
        if weekday < 5:  # Mon=0 … Fri=4
            count += 1
    return count


def working_days_from(start: date, year: int, month: int) -> int:
    """Working days from `start` (inclusive) to end of month."""
    _, days_in_month = calendar.monthrange(year, month)
    end = date(year, month, days_in_month)
    count = 0
    current = max(start, date(year, month, 1))
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current = date(current.year, current.month, current.day + 1) \
            if current.day < days_in_month else date(year, month, days_in_month + 1)  # break
    return count


def working_days_from_to(start: date, end: date) -> int:
    """Working days between start and end (inclusive)."""
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        from datetime import timedelta
        current += timedelta(days=1)
    return count


def calculate_payslip(
    employee,
    year: int,
    month: int,
    unpaid_leave_days: float = 0.0,
) -> dict:
    """
    Compute all payslip figures for one employee in a given period.

    Parameters
    ----------
    employee    : Employee ORM instance
    year        : payroll year
    month       : payroll month (1-12)
    unpaid_leave_days : days of unpaid leave taken this period

    Returns
    -------
    dict with all payslip fields
    """
    _, days_in_month_cal = calendar.monthrange(year, month)
    total_working_days = working_days_in_month(year, month)

    # ---- Pro-ration for mid-month joiners ----
    start = employee.start_date
    joined_this_month = (start.year == year and start.month == month)

    if joined_this_month:
        # Count working days from join date to end of month
        days_worked = working_days_from_to(start, date(year, month, days_in_month_cal))
        notes = f"Mid-month joiner ({start}); worked {days_worked}/{total_working_days} working days."
    else:
        days_worked = float(total_working_days)
        notes = ""

    # ---- Unpaid leave deduction ----
    daily_rate = employee.salary / total_working_days
    unpaid_leave_deduction = round(daily_rate * unpaid_leave_days, 2)

    # ---- Prorated gross ----
    if joined_this_month:
        prorated_gross = round((employee.salary / total_working_days) * days_worked, 2)
    else:
        prorated_gross = employee.salary

    prorated_gross -= unpaid_leave_deduction
    prorated_gross = max(0.0, round(prorated_gross, 2))

    # ---- Social Security ----
    social_security = round(compute_social_security(prorated_gross), 2)

    # ---- Taxable Income ----
    taxable_income = max(0.0, round(prorated_gross - social_security, 2))

    # ---- Income Tax ----
    income_tax = compute_income_tax(taxable_income)

    # ---- Total Deductions & Net Pay ----
    total_deductions = round(social_security + income_tax, 2)
    net_pay = round(prorated_gross - total_deductions, 2)

    return {
        'gross_salary': employee.salary,
        'days_in_month': total_working_days,
        'days_worked': days_worked,
        'prorated_gross': prorated_gross,
        'unpaid_leave_days': unpaid_leave_days,
        'unpaid_leave_deduction': unpaid_leave_deduction,
        'taxable_income': taxable_income,
        'income_tax': income_tax,
        'social_security': social_security,
        'total_deductions': total_deductions,
        'net_pay': net_pay,
        'notes': notes,
    }
