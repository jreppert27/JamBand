import os
from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import login_user, logout_user, current_user, login_required
import sqlalchemy as sa
from app import app, db
from app.forms import LoginForm, RegistrationForm, \
    EmptyForm, ResetPasswordRequestForm, ResetPasswordForm, PostForm
from app.models import User, Post, Group
from app.email import send_password_reset_email
from werkzeug.utils import secure_filename

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

@app.route('/reset_db')
def reset_db():
    flash("Resetting database: deleting old data and repopulating with dummy data")
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        print(f'Clearing table {table}')
        db.session.execute(table.delete())
    db.session.commit()

    # Create users
    u1 = User(username="Gavin", email="gavin@garver.org")
    u1.set_password("Gavinpassword")

    u2 = User(username="Jack", email="jackreppert@gmail.com")
    u2.set_password("Jackpassword")

    u3 = User(username="Bob", email="bob@email.com")
    u3.set_password("Bobpassword")

    db.session.add_all([u1, u2, u3])
    db.session.commit()

    # Create some posts
    p1 = Post(header="My first post", body="This is my first post", author=u1)
    p2 = Post(header="Cool thing",   body="This is a cool thing here", author=u2)
    p3 = Post(header="My Second post", body="This is my second post", author=u1)
    p4 = Post(header="Hello world!", body="Hello there", author=u3)

    db.session.add_all([p1, p2, p3, p4])
    db.session.commit()

    # Create groups
    g1 = Group(name='The creators',
               bio='We made this',
               members=[u1, u2])     # Gavin & Jack

    g2 = Group(name='The created',
               bio='We were made here',
               members=[u3])         # Bob

    # New group just for Jack
    g3 = Group(name="Jack's Group",
               bio="A special group for Jack",
               members=[u2])         # Jack

    db.session.add_all([g1, g2, g3])
    db.session.commit()

    return redirect(url_for('index'))



@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.is_authenticated and form.validate_on_submit():
        post = Post(
            header=form.header.data if hasattr(form, 'header') else "New Post",
            body=form.post.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    if current_user.is_authenticated:
        posts = db.paginate(current_user.following_posts(), page=page,
                            per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    else:
        posts = db.paginate(
            sa.select(Post).order_by(Post.timestamp.desc()),
            page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False
        )
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('home.html', title='Home')


@app.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    # Retrieve the user profile.
    user_obj = User.query.filter_by(username=username).first_or_404()

    # Process form submission.
    if request.method == 'POST':
        # Only the owner can update their profile.
        if current_user.id != user_obj.id:
            abort(403)

        # Update the bio.
        new_bio = request.form.get('about_me', '')
        user_obj.about_me = new_bio

        # Process media file if one was uploaded.
        media_file = request.files.get('media_upload')
        if media_file and media_file.filename != "":
            filename = secure_filename(media_file.filename)
            media_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            media_file.save(media_path)
            # You can save the media_path or filename to the database associated with the user.
            flash('Media uploaded successfully!', 'info')

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('user', username=user_obj.username))

    # For GET requests, also pass the user's groups (if any).
    groups = user_obj.groups
    return render_template(
        'profile.html',
        title=f"{user_obj.username}'s Profile",
        user=user_obj,
        groups=groups
    )
@app.route('/group/<int:group_id>')
@login_required
def group(group_id):
    group_obj = db.session.get(Group, group_id) or abort(404)
    members = group_obj.members  # assumes this relationship is now readable
    return render_template(
        'group.html',
        title=group_obj.name,
        group=group_obj,
        members=members
    )