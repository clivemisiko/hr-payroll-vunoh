from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth import bp as auth_bp
    from app.main import bp as main_bp
    from app.employees import bp as employees_bp
    from app.leave import bp as leave_bp
    from app.payroll import bp as payroll_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(leave_bp, url_prefix='/leave')
    app.register_blueprint(payroll_bp, url_prefix='/payroll')

    from datetime import datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    with app.app_context():
        db.create_all()
        from app.utils.seed import seed_data
        seed_data()

    return app
