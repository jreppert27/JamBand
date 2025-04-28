# app/errors/__init__.py
from flask import Blueprint

bp = Blueprint('errors', __name__)

from . import handlers    # ← relative, no “app.errors” here
