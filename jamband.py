import sqlalchemy as sa
import sqlalchemy.orm as so

from flask_migrate import Migrate              # <<–– add this
from app import app, db
from app.models import User, Post

# Initialize Flask‑Migrate
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return {
        'sa': sa,
        'so': so,
        'db': db,
        'User': User,
        'Post': Post,
        # add more models here as needed…
    }
