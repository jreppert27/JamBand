# app/__init__.py
import logging, os
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
from elasticsearch import Elasticsearch
from flask_wtf import CSRFProtect
from redis import Redis
import rq

# from app.forms import *
# from app.models import *
from config import Config
from flask import Blueprint

db        = SQLAlchemy()
migrate   = Migrate()        # ← no app passed here
login     = LoginManager()
mail      = Mail()
bootstrap = Bootstrap()
moment    = Moment()
babel     = Babel()
bp = Blueprint('auth', __name__)
csrf      = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # bind extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    csrf.init_app(app)

    # safe ES / Redis
    es_url = app.config.get('ELASTICSEARCH_URL')
    app.elasticsearch = Elasticsearch([es_url]) if es_url else None

    redis_url = app.config.get('REDIS_URL')
    app.redis = Redis.from_url(redis_url) if redis_url else None

    # register blueprints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    login.login_view = 'auth.login'

    # logging handlers (only after app exists)
    if not app.debug:
        if app.config['MAIL_SERVER']:
            auth   = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']) \
                         if app.config['MAIL_USERNAME'] else None
            secure = () if app.config['MAIL_USE_TLS'] else None
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='JamBand Failure',
                credentials=auth, secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/jamband.log',
                                           maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('JamBand startup')

    from .forms import GroupForm, PostForm, CommentForm, FollowButton
    @app.context_processor
    def inject_group_form():
        return {'group_form': GroupForm(),
                'post_form': PostForm(),
                'comment_form': CommentForm(),
                'follow_form': FollowButton()}

    return app
