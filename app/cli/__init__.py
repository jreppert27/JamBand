from flask import Blueprint

bp = Blueprint('cli', __name__)

from app.cli import commands

from .commands import create_user

def register_cli(app):
    """Attach custom Click commands to the Flask app."""
    app.cli.add_command(create_user)
