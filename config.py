import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vunoh-hr-dev-secret-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'vunoh_hr.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Leave rules
    LEAVE_MIN_NOTICE_DAYS = 3          # minimum days notice for non-emergency leave
    LEAVE_MAX_CONSECUTIVE_DAYS = 21    # max consecutive days in one request
    LEAVE_MIN_TEAM_COVERAGE = 2        # minimum team members present during leave
    LEAVE_ESCALATION_DAYS = 2          # escalate if unanswered after N days
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
