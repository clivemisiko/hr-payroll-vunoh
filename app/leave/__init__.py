from flask import Blueprint

bp = Blueprint('leave', __name__)

from app.leave import routes  # noqa
