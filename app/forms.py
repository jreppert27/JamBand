# from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
#     TextAreaField
# from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
#     Length, Optional
# import sqlalchemy as sa
# from app.models import *
#
# class LoginForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     remember_me = BooleanField('Remember Me')
#     submit = SubmitField('Sign In')
#
# class RegistrationForm(FlaskForm):
#     username = StringField('Username', validators=[DataRequired()])
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     password = PasswordField('Password', validators=[DataRequired()])
#     password2 = PasswordField(
#         'Repeat Password', validators=[DataRequired(), EqualTo('password')])
#     submit = SubmitField('Register')
#
#     def validate_password(self, password):
#         user = db.session.scalar(sa.select(User).where(
#             User.password_hash == password.data))
#         if user is not None:
#             raise ValidationError('Please use a different password.')
#
#     def validate_username(self, username):
#         user = db.session.scalar(sa.select(User).where(
#             User.username == username.data))
#         if user is not None:
#             raise ValidationError('Please use a different username.')
#
#     def validate_email(self, email):
#         user = db.session.scalar(sa.select(User).where(
#             User.email == email.data))
#         if user is not None:
#             raise ValidationError('Please use a different email address.')
#
# class ResetPasswordRequestForm(FlaskForm):
#     email = StringField('Email', validators=[DataRequired(), Email()])
#     submit = SubmitField('Request Password Reset')
#
# class ResetPasswordForm(FlaskForm):
#     password = PasswordField('Password', validators=[DataRequired()])
#     password2 = PasswordField(
#         'Repeat Password', validators=[DataRequired(), EqualTo('password')])
#     submit = SubmitField('Request Password Reset')
#
# class EmptyForm(FlaskForm):
#     submit = SubmitField('Submit')

# class PostForm(FlaskForm):
#     header = StringField('Title', validators=[
#         DataRequired(), Length(min=1, max=140)])
#     post = TextAreaField('Say something', validators=[
#         DataRequired(), Length(min=1, max=140)])
#     submit = SubmitField('Submit')
#
# class FollowButton(FlaskForm):
#     submit = SubmitField('Follow')
#
# class CommentForm(FlaskForm):
#     comment_body = TextAreaField('Comment', validators=[DataRequired()])
#     submit       = SubmitField('Submit')
#
#
# class GroupForm(FlaskForm):
#     name = StringField(
#         'Group Name',
#         validators=[DataRequired(), Length(max=64)]
#     )
#     bio = TextAreaField(
#         'Bio / Description',
#         validators=[DataRequired(), Length(max=256)]
#     )
#     submit = SubmitField('Create Group')