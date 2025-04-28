import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db, bp
from app.models import (
    User, Post, Comment,
    Group, GroupMembers, GroupFollowers,
    Tag, Tags
)

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'sa': sa,
        'bp': bp,
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
    # pick host/port as you like; debug=True gives auto-reload + debug console
    app.run(host='127.0.0.1', port=5000, debug=True)
