import click
from app import db
from app.models import User

@click.command('create-user')
@click.argument('email')
def create_user(email):
    """Create a new user with the given EMAIL."""
    user = User(email=email)
    db.session.add(user)
    db.session.commit()
    click.echo(f'✅  User {email} created!')
