# app/auth/email.py

from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from app import mail

def _send_async_email(app, msg):
    # we were passed the real app object, so we can push its context
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body

    # grab the actual Flask app so our thread can push its context
    app = current_app._get_current_object()
    Thread(target=_send_async_email, args=(app, msg)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        subject='[JamBand] Reset Your Password',
        sender=current_app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt', user=user, token=token),
        html_body=render_template('email/reset_password.html', user=user, token=token)
    )
