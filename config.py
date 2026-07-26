import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Detect serverless environment (Vercel, AWS Lambda, etc.)
IS_SERVERLESS = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))


def _get_database_uri():
    """Resolve the database URI with fallback to local SQLite."""
    uri = os.environ.get('DATABASE_URL')
    if uri:
        # Fix Neon / Heroku 'postgres://' → 'postgresql://' (SQLAlchemy 2.x requirement)
        if uri.startswith('postgres://'):
            uri = uri.replace('postgres://', 'postgresql://', 1)
        return uri

    # Fallback: local SQLite (development only)
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    return f'sqlite:///{os.path.join(instance_dir, "vunoh_hr.db")}'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vunoh-hr-dev-secret-change-in-production'

    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings for serverless (Neon uses connection pooling)
    if IS_SERVERLESS:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,     # Verify connections are alive before use
            'pool_recycle': 300,       # Recycle connections every 5 min
            'pool_size': 5,
            'max_overflow': 10,
        }

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

