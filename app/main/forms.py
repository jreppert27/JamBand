from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField
from wtforms.fields.choices import SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length, Optional
import sqlalchemy as sa
from app.models import *


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')

class PostForm(FlaskForm):
    group_id = SelectField('Post To', coerce=int, validators=[DataRequired()])
    header   = StringField('Title',    validators=[DataRequired()])
    body     = TextAreaField('Text',   validators=[DataRequired()])
    media    = FileField('Media (optional)')
    submit   = SubmitField('Post')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # start with the “Your Profile” option
        choices = [(0, 'Your Profile')]

        # only add real groups if there’s a logged-in user
        if current_user.is_authenticated:
            # current_user.groups should exist now
            choices += [(g.id, g.name) for g in current_user.groups]

        self.group_id.choices = choices

class FollowButton(FlaskForm):
    submit = SubmitField('Follow')

class FollowGroupForm(FlaskForm):
    submit = SubmitField()
    class Meta:
        csrf = False

class CommentForm(FlaskForm):
    comment_body = TextAreaField('Comment', validators=[DataRequired()])
    submit       = SubmitField('Submit')


class GroupForm(FlaskForm):
    name = StringField(
        'Group Name',
        validators=[DataRequired(), Length(max=64)]
    )
    bio = TextAreaField(
        'Bio / Description',
        validators=[DataRequired(), Length(max=256)]
    )
    submit = SubmitField('Create Group')

class EditProfileForm(FlaskForm):
    profile_picture = FileField(
        'Profile Picture',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')]
    )
    profile_banner = FileField(
        'Profile Banner',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')]
    )
    about_me = TextAreaField(
        'About Me',
        validators=[Length(max=140, message="140 characters max")]
    )
    submit = SubmitField('Save Changes')