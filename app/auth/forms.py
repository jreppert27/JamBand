from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length, Optional, Regexp
import sqlalchemy as sa
from app.models import *

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[
        DataRequired(),
        Regexp(r'.+@.+\..+', message='Enter a valid email address')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_password(self, password):
        user = db.session.scalar(sa.select(User).where(
            User.password_hash == password.data))
        if user is not None:
            raise ValidationError('Please use a different password.')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class EditProfileForm(FlaskForm):
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    profile_picture = FileField('Profile Picture',
                               validators=[FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])
    profile_banner = FileField('Profile Banner',
                              validators=[FileAllowed(['jpg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Submit')

class FollowButton(FlaskForm):
    submit = SubmitField('Follow')

class PostForm(FlaskForm):
    header = StringField('Title', validators=[Length(min=0, max=140)])
    post = TextAreaField('Body', validators=[DataRequired(), Length(min=1, max=140)])
    body = TextAreaField('Body', validators=[Length(min=0, max=140)])
    media = FileField('Media (optional)',
                     validators=[FileAllowed(['jpg', 'png', 'gif', 'mp3', 'mp4'], 'Media files only!')])
    # FIX: Use Optional without parentheses
    group_id = SelectField('Post to', coerce=int, validators=[Optional])
    submit = SubmitField('Post')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # Populate the groups dropdown - will need to be set later
        self.group_id.choices = [(0, 'Personal (My Profile)')]

class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired(), Length(min=1, max=64)])
    bio = TextAreaField('Description', validators=[Length(min=0, max=256)])
    submit = SubmitField('Create Group')

class FollowGroupForm(FlaskForm):
    submit = SubmitField('Follow Group')