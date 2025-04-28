from flask import render_template, request, current_app
from . import bp

@bp.app_errorhandler(404)
def not_found_error(error):
    current_app.logger.warning(f"404 – path: {request.path}")
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def internal_error(error):
    current_app.logger.error("500 – internal error", exc_info=error)
    return render_template('500.html'), 500