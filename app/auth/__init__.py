from flask import Blueprint

bp = Blueprint('auth', __name__)

# import the view‐functions so they get registered on bp
from app.auth import routes
