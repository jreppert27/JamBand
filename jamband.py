import sqlalchemy as sa
import sqlalchemy.orm as so

from flask_migrate import Migrate              # <<–– add this
from app import app, db
import app
import app.routes
from app.models import (
    User, Post, Comment,
    Group, GroupMembers, GroupFollowers,
    Tag, Tags
)

@app.shell_context_processor
def make_shell_context():
    return {
        'sa': sa,
        'so': so,
        'db': db,
        'User': User,
        'Post': Post,
        'Comment': Comment,
        'Group': Group,
        'GroupMembers': GroupMembers,
        'GroupFollowers': GroupFollowers,
        'Tag': Tag,
        'Tags': Tags,
    }
