# jamband.py
import sqlalchemy as sa
import sqlalchemy.orm as so

from app import create_app, db
from app.models import (
    User, Post, Comment,
    Group, GroupMembers, GroupFollowers,
    Tag, Tags
)

# create the Flask app
app = create_app()

# make your models & db available in flask shell
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

if __name__ == '__main__':
    # Run with debug=True during development
    app.run(host='127.0.0.1', port=5000, debug=True)
