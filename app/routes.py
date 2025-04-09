from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa
from app import app, db
from app.forms import LoginForm, RegistrationForm, \
    EmptyForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Post
from app.email import send_password_reset_email

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template(index.html, title='Home')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#
# @app.route('/logout', methods=['GET', 'POST'])
# def logout():
#
# @app.route('/register', methods=['GET', 'POST'])
# def register():