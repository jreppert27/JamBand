# app/api/routes.py
from flask import jsonify, request
from . import bp
from app.models import User  # import only what you need

@bp.route('/things')
def get_things():
    data = User.query.all()
    return jsonify([x.to_dict() for x in data])
