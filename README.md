# Vunoh Global HR & Payroll Platform

A full-featured internal HR and Payroll application built with Python Flask, PostgreSQL (Neon) / SQLite (SQLAlchemy), and modern HTML5/Vanilla CSS/JS, designed specifically according to Vunoh Global's design system and real-world business logic requirements.

---

## 🌟 Key Prioritization & Architecture Decisions

When managing team records, leave, and payroll over spreadsheets, real-world operational problems arise. This platform prioritises **robust business logic**, **data integrity**, and **seamless automation** over simple CRUD forms:

1. **Employee Records & Persistence:**
   - Soft-deactivation (`is_active = False`) instead of hard deletion. This ensures that past payslips and financial audit trails remain 100% intact even after an employee leaves.
   - Comprehensive reporting lines and org hierarchy visualization.

2. **Leave Management Safeguards:**
   - **Under-coverage Prevention:** Automatically checks if approving a request drops active team coverage below the configured minimum (`LEAVE_MIN_TEAM_COVERAGE`).
   - **Notice Period Requirement:** Flagged warnings for requests submitted with insufficient lead time (`LEAVE_MIN_NOTICE_DAYS`), allowing managers to review before overriding.
   - **Overdue Request Escalation:** Automatic status escalation (`escalated`) for pending requests left unanswered past the escalation threshold (`LEAVE_ESCALATION_DAYS`).
   - **Consecutive Days Cap:** Enforces a maximum limit on single continuous leave requests (`LEAVE_MAX_CONSECUTIVE_DAYS`).
   - **Seamless Payroll Link:** Approved unpaid leave automatically flows into the payroll calculation engine to deduct daily pay rates.

3. **Payroll Engine Edge Case Handling:**
   - **Mid-Month Joiners:** Pro-rated based on exact working days (Mon–Fri) remaining in the join month.
   - **Progressive Tax Brackets:** Statutory income tax calculated on taxable income (Prorated Gross minus Social Security) using progressive brackets.
   - **Statutory Deduction Caps:** Employee Social Security contribution capped at KES 4,500.
   - **Zero-Deduction Bounds:** Handles zero or low-income threshold brackets smoothly.

---

## 🛠 Tech Stack

- **Backend:** Python 3.12, Flask, Flask-SQLAlchemy, Flask-Login, Pytest
- **Frontend:** HTML5, Modern Vanilla CSS3 (Custom design system based on [Vunoh Global](https://www.vunohglobal.com/)), Vanilla JavaScript
- **Database:** PostgreSQL (Neon Cloud Database for Production/Vercel) / SQLite (`vunoh_hr.db` for local dev), with exported SQL dump file (`schema_and_seed_dump.sql`)

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.12+ installed

### Step-by-step Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/clivemisiko/hr-payroll-vunoh.git
   cd hr-payroll-vunoh
   ```

2. **Create a virtual environment & install dependencies:**
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Run the Application:**
   ```bash
   python run.py
   ```
   The application will initialize SQLite database `vunoh_hr.db` locally (or connect to PostgreSQL if `DATABASE_URL` is set in `.env`) and automatically seed realistic sample data on first launch.
   Access the web interface at **`http://127.0.0.1:5050`**.

4. **Run Unit & Integration Tests:**
   ```bash
   pytest tests/test_business_logic.py
   ```

---

## 🔐 Credentials for Demo Testing

The application includes an unauthenticated public Landing Page (`/`) and Role-Based Authentication (`/auth/login`). You can log in using any of the seeded accounts below:

| Role | Username | Password | Notes |
|---|---|---|---|
| **Admin** | `admin` | `Admin@1234` | Full access to employees, leave approvals, and payroll generation |
| **Manager (Engineering)** | `brian.kamau` | `Eng@1234` | Manages software engineering team & leave approvals |
| **Manager (HR)** | `amina.ochieng` | `Hr@1234` | HR Manager approvals |
| **Employee** | `alice.njeri` | `Alice@1234` | Submits leave requests, views personal payslips & balances |
| **Employee** | `bob.otieno` | `Bob@1234` | Submits leave requests, views personal payslips & balances |

---

## 📊 Statutory Tax & Payroll Formula

```text
Working Days Daily Rate = Base Salary / Total Working Days in Month
Unpaid Leave Deduction = Daily Rate * Approved Unpaid Leave Days
Prorated Gross = (Daily Rate * Working Days Worked) - Unpaid Leave Deduction

Social Security (6%) = Min(Prorated Gross * 0.06, 4500.0)
Taxable Income = Max(0.0, Prorated Gross - Social Security)

Progressive Monthly Tax Brackets:
  • KES 0 – 15,000      : 0%
  • KES 15,001 – 30,000 : 10% on portion in bracket
  • KES 30,001 – 60,000 : 20% on portion in bracket
  • KES 60,001+         : 30% on portion in bracket

Total Deductions = Social Security + Income Tax
Net Take-Home Pay = Prorated Gross - Total Deductions
```

---

## 🔮 Future Improvements Given More Time

1. **Multi-currency & Global Localization:** Expand statutory tax profiles by country.
2. **Automated PDF Payslip Downloads:** Server-side PDF generation (e.g. WeasyPrint) for email distribution.
3. **Automated Reminders & Email/Slack Webhooks:** Instant notifications when leave requests are submitted or escalated.
