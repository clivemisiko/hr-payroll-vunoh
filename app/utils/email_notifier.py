import smtplib
import threading
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)

def _send_async_email(app, recipient, subject, html_body):
    """Background worker function to send email via SMTP."""
    with app.app_context():
        mail_server = app.config.get('MAIL_SERVER')
        mail_port = app.config.get('MAIL_PORT')
        mail_username = app.config.get('MAIL_USERNAME')
        mail_password = (app.config.get('MAIL_PASSWORD') or '').replace(' ', '').strip()
        mail_sender = app.config.get('MAIL_DEFAULT_SENDER') or mail_username

        if not mail_username or not mail_password:
            logger.info(f"[Email Notification Mock] To: {recipient} | Subject: {subject}\nBody: {html_body[:100]}...")
            print(f"📧 [Email Mock] Notification to {recipient}: '{subject}' (Set MAIL_USERNAME & MAIL_PASSWORD in .env to send real emails)")
            return

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Vunoh HR Platform <{mail_sender}>"
            msg['To'] = recipient

            part = MIMEText(html_body, 'html')
            msg.attach(part)

            server = smtplib.SMTP(mail_server, mail_port, timeout=10)
            if app.config.get('MAIL_USE_TLS'):
                server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(mail_sender, [recipient], msg.as_string())
            server.quit()
            print(f"✅ Email successfully sent to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            print(f"⚠️ Email send failed for {recipient}: {e}")


def send_leave_status_email(employee_email, employee_name, leave_type_name, start_date, end_date, status, reason=None):
    """
    Sends asynchronous leave status update email (Approved / Rejected) to employee.
    Does not block HTTP thread.
    """
    if not employee_email:
        return

    is_approved = status.lower() == 'approved'
    status_color = "#10b981" if is_approved else "#ef4444"
    status_title = "Approved 🎉" if is_approved else "Rejected"

    subject = f"Leave Request {status.capitalize()} — Vunoh HR"

    reason_html = f"<p style='color:#7f1d1d;background:#fee2e2;padding:12px;border-radius:6px;'><strong>Reason:</strong> {reason}</p>" if reason and not is_approved else ""

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; color: #1a202c; background-color: #f8fafc; padding: 20px;">
      <div style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 30px; border: 1px solid #e2e8f0;">
        <div style="background: linear-gradient(135deg, #01264c, #1B75BB); padding: 18px 24px; border-radius: 8px; color: #ffffff; text-align: center; margin-bottom: 24px;">
          <h2 style="margin: 0; font-size: 20px;">Vunoh Global HR</h2>
        </div>
        <p style="font-size: 16px;">Hello <strong>{employee_name}</strong>,</p>
        <p>Your leave request has been reviewed by management:</p>
        
        <div style="background: #f1f5f9; padding: 16px; border-radius: 8px; margin: 20px 0;">
          <p style="margin: 4px 0;"><strong>Leave Type:</strong> {leave_type_name}</p>
          <p style="margin: 4px 0;"><strong>Dates:</strong> {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}</p>
          <p style="margin: 4px 0;"><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold; font-size: 16px;">{status_title}</span></p>
        </div>

        {reason_html}

        <p style="font-size: 14px; color: #64748b; margin-top: 24px;">You can view your complete leave record and balances in your <a href="http://127.0.0.1:5050" style="color: #1B75BB;">Vunoh HR Dashboard</a>.</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin-top: 24px;"/>
        <p style="font-size: 12px; color: #94a3b8; text-align: center;">This is an automated notification from Vunoh Global HR Platform.</p>
      </div>
    </body>
    </html>
    """

    app = current_app._get_current_object()
    thread = threading.Thread(target=_send_async_email, args=(app, employee_email, subject, html_body))
    thread.daemon = True
    thread.start()
