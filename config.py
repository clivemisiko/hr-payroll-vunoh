import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Detect serverless environment (Vercel, AWS Lambda, etc.)
IS_SERVERLESS = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vunoh-hr-dev-secret-change-in-production'

    # On Vercel/serverless: filesystem is read-only except /tmp
    if IS_SERVERLESS:
        _db_path = '/tmp/vunoh_hr.db'
    else:
        _instance_dir = os.path.join(basedir, 'instance')
        os.makedirs(_instance_dir, exist_ok=True)
        _db_path = os.path.join(_instance_dir, 'vunoh_hr.db')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{_db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Business Rule Limits
    LEAVE_MIN_NOTICE_DAYS = int(os.environ.get('LEAVE_MIN_NOTICE_DAYS', 3))
    LEAVE_MAX_CONSECUTIVE_DAYS = int(os.environ.get('LEAVE_MAX_CONSECUTIVE_DAYS', 21))
    LEAVE_MIN_TEAM_COVERAGE = float(os.environ.get('LEAVE_MIN_TEAM_COVERAGE', 0.50))
    LEAVE_ESCALATION_DAYS = int(os.environ.get('LEAVE_ESCALATION_DAYS', 2))

    # Email SMTP Settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # Annual leave entitlement by employment type
    ANNUAL_LEAVE_DAYS = {
        'full_time': 21,
        'part_time': 10,
        'contract': 10,
        'intern': 5,
    }


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret'
