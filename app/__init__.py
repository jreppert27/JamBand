# app/__init__.py
import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler

import rq
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel
from flask_wtf import CSRFProtect
from elasticsearch import Elasticsearch
from redis import Redis

from config import Config

# instantiate extensions without an app
db        = SQLAlchemy()
migrate   = Migrate()
login     = LoginManager()
mail      = Mail()
bootstrap = Bootstrap()
moment    = Moment()
babel     = Babel()
csrf      = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)       # now Migrate will register its CLI commands
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    csrf.init_app(app)

    # optional: Elasticsearch & Redis clients
    if app.config.get('ELASTICSEARCH_URL'):
        app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']])
    else:
        app.elasticsearch = None

    if app.config.get('REDIS_URL'):
        app.redis = Redis.from_url(app.config['REDIS_URL'])
        app.task_queue = rq.Queue('default', connection=app.redis)
    else:
        app.redis = None

    # register your blueprints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)    # your index and create_post live here

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # login settings
    login.login_view = 'auth.login'
    login.login_message = "Please log in to access this page."

    # logging (email on errors, rotating file)
    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = () if app.config['MAIL_USE_TLS'] else None
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'],
                subject='JamBand Application Error',
                credentials=auth,
                secure=secure
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

    # inject your form objects into all templates
    from app.main.forms import GroupForm, PostForm, CommentForm, FollowButton, EditProfileForm
    @app.context_processor
    def inject_forms():
        return {
            'group_form': GroupForm(),
            'post_form': PostForm(),
            'comment_form': CommentForm(),
            'follow_form': FollowButton(),
            'edit_profile_form': EditProfileForm()
        }

    return app
