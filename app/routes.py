# import os
# from urllib.parse import urlsplit
# from flask import render_template, flash, redirect, url_for, abort
# from flask_login import login_user, logout_user, current_user, login_required
# from app import app
# from app.forms import *
# from app.models import *
# from app.auth.email import send_password_reset_email
# from werkzeug.utils import secure_filename

# app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

# @app.route('/reset_db')
# def reset_db():
#     flash("Resetting database: deleting old data and repopulating with dummy data")
#
#     # 1) Wipe all tables
#     meta = db.metadata
#     for table in reversed(meta.sorted_tables):
#         db.session.execute(table.delete())
#     db.session.commit()
#
#     # 2) Create users
#     u1 = User(username="Gavin", email="gavin@garver.org")
#     u1.set_password("Gavinpassword")
#     u2 = User(username="Jack",  email="jackreppert@gmail.com")
#     u2.set_password("Jackpassword")
#     u3 = User(username="Bob",   email="bob@email.com")
#     u3.set_password("Bobpassword")
#
#     db.session.add_all([u1, u2, u3])
#     db.session.commit()
#
#     # 3) Make some follow relationships
#     u1.follow(u2)   # Gavin follows Jack
#     u2.follow(u1)   # Jack follows Gavin
#     u3.follow(u1)   # Bob follows Gavin
#     db.session.commit()
#
#     # 4) Create groups
#     g1 = Group(name="The Creators", bio="We built this app")
#     g2 = Group(name="The Created",  bio="Here to test & give feedback")
#     g3 = Group(name="Jack's Circle", bio="Jack's special crew")
#
#     db.session.add_all([g1, g2, g3])
#     db.session.commit()
#
#     # 5) Assign members to groups
#     gm1 = GroupMembers(user_id=u1.id, group_id=g1.id, role="admin")
#     gm2 = GroupMembers(user_id=u2.id, group_id=g1.id, role="member")
#     gm3 = GroupMembers(user_id=u3.id, group_id=g2.id, role="admin")
#     gm4 = GroupMembers(user_id=u2.id, group_id=g3.id, role="admin")
#     db.session.add_all([gm1, gm2, gm3, gm4])
#     db.session.commit()
#
#     # 6) Some users follow groups
#     gf1 = GroupFollowers(user_id=u3.id, group_id=g1.id)  # Bob follows g1
#     gf2 = GroupFollowers(user_id=u1.id, group_id=g2.id)  # Gavin follows g2
#     db.session.add_all([gf1, gf2])
#     db.session.commit()
#
#     # 7) Create posts (some personal, some in groups)
#     p1 = Post(header="Gavin’s first post", body="Hello from Gavin!", author=u1)
#     p2 = Post(header="Jack’s news",    body="Jack just joined our group", author=u2, group=g1)
#     p3 = Post(header="Bob asks",       body="How do I reset the DB?", author=u3)
#     p4 = Post(header="Group shout",    body="Welcome new members!", author=u1, group=g1)
#     p5 = Post(header="Circle chat",    body="Jack's inner circle discussion", author=u2, group=g3)
#
#     db.session.add_all([p1, p2, p3, p4, p5])
#     db.session.commit()
#
#     # 8) Comments and a nested reply
#     c1 = Comment(body="Nice post, Gavin!", author=u2, post=p1)
#     c2 = Comment(body="Thanks Jack!",      author=u1, post=p1, parent=c1)
#     c3 = Comment(body="Welcome all!",       author=u3, post=p4)
#     db.session.add_all([c1, c2, c3])
#     db.session.commit()
#
#     return redirect(url_for('index'))

# app.route('/', methods=['GET', 'POST'])
# @app.route('/index', methods=['GET', 'POST'])
# @login_required
# def index():
#     form = PostForm()
#     if form.validate_on_submit():
#         post = Post(
#             header=form.header.data or "New Post",
#             body=form.body.data,
#             author=current_user
#         )
#         # handle media & group_id exactly as before...
#         db.session.add(post)
#         db.session.commit()
#         flash('Your post is now live!')
#         return redirect(url_for('index'))
#
#     # Decide which posts to show
#     view = request.args.get('view', 'following')
#     if view == 'following':
#         query = current_user.following_posts()
#     else:
#         query = sa.select(Post).order_by(Post.timestamp.desc())
#
#     # Fetch ALL matching posts
#     posts = db.session.scalars(query).all()
#
#     return render_template(
#         'index.html',
#         title='Home',
#         form=form,
#         posts=posts,
#         view=view
#     )

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = LoginForm()
#     if form.validate_on_submit():
#         user = db.session.scalar(
#             sa.select(User).where(User.username == form.username.data))
#         if user is None or not user.check_password(form.password.data):
#             flash('Invalid username or password')
#             return redirect(url_for('login'))
#         login_user(user, remember=form.remember_me.data)
#         next_page = request.args.get('next')
#         if not next_page or urlsplit(next_page).netloc != '':
#             next_page = url_for('index')
#         return redirect(next_page)
#     return render_template('login.html', title='Sign In', form=form)
#
# @app.route('/logout', methods=['GET', 'POST'])
# def logout():
#     logout_user()
#     return redirect(url_for('index'))
#
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         user = User(username=form.username.data, email=form.email.data)
#         user.set_password(form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         flash('Congratulations, you are now a registered user!')
#         return redirect(url_for('login'))
#     return render_template('register.html', title='Register', form=form)
#
# @app.route('/reset_password_request', methods=['GET', 'POST'])
# def reset_password_request():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = ResetPasswordRequestForm()
#     if form.validate_on_submit():
#         user = db.session.scalar(
#             sa.select(User).where(User.email == form.email.data))
#         if user:
#             send_password_reset_email(user)
#         flash('Check your email for the instructions to reset your password')
#         return redirect(url_for('login'))
#     return render_template('reset_password_request.html',
#                            title='Reset Password', form=form)

# @app.route('/user/<username>', methods=['GET', 'POST'])
# @login_required
# def user(username):
#     user_obj = User.query.filter_by(username=username).first_or_404()
#
#     # instantiate the follow/unfollow form
#     form = FollowButton()
#     is_following = current_user.is_following(user_obj)
#
#     # Only non-owners can hit the follow/unfollow POST
#     if user_obj != current_user and form.validate_on_submit():
#         if is_following:
#             current_user.unfollow(user_obj)
#             flash(f'You have unfollowed {user_obj.username}.', 'info')
#         else:
#             current_user.follow(user_obj)
#             flash(f'You are now following {user_obj.username}.', 'success')
#         db.session.commit()
#         return redirect(url_for('user', username=username))
#
#     # Profile‐edit logic (unchanged)
#     if request.method == 'POST' and user_obj == current_user:
#         new_bio = request.form.get('about_me', '')
#         user_obj.about_me = new_bio
#
#         media_file = request.files.get('media_upload')
#         if media_file and media_file.filename:
#             filename = secure_filename(media_file.filename)
#             media_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             media_file.save(media_path)
#             flash('Media uploaded successfully!', 'info')
#
#         db.session.commit()
#         flash('Your profile has been updated.', 'success')
#         return redirect(url_for('user', username=username))
#
#     groups = user_obj.groups
#     return render_template(
#         'profile.html',
#         title=f"{user_obj.username}'s Profile",
#         user=user_obj,
#         groups=groups,
#         form=form,
#         is_following=is_following
#     )
# @app.route('/group/<int:group_id>')
# @login_required
# def group(group_id):
#     group_obj = db.session.get(Group, group_id) or abort(404)
#     members = group_obj.members  # assumes this relationship is now readable
#     return render_template(
#         'group.html',
#         title=group_obj.name,
#         group=group_obj,
#         members=members
#     )

# @app.route('/create_post', methods=['POST'])
# @login_required
# def create_post():
#     header = request.form.get('header','').strip()
#     body   = request.form.get('body','').strip()
#     if not header or not body:
#         flash('Title and text are required.', 'danger')
#         return redirect(request.referrer or url_for('index'))
#
#     post = Post(header=header, body=body, author=current_user)
#
#     media = request.files.get('media')
#     if media and media.filename:
#         filename = secure_filename(media.filename)
#         save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         media.save(save_path)
#         # *** assign to post.media_path ***
#         post.media_path = filename
#
#     group_id = request.form.get('group_id').strip()
#     if group_id:
#         try:
#             post.group_id = int(group_id)
#         except ValueError:
#             pass
#
#     db.session.add(post)
#     db.session.commit()
#     flash('Your post has been created!', 'success')
#     return redirect(request.referrer or url_for('index'))

# @app.route('/post/<int:post_id>/comment', methods=['POST'])
# @login_required
# def comment_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     body = request.form.get('comment_body','').strip()
#     if not body:
#         flash('Comment cannot be empty.', 'danger')
#         return redirect(request.referrer or url_for('index'))
#     c = Comment(body=body, author=current_user, post=post)
#     db.session.add(c)
#     db.session.commit()
#     flash('Your comment was posted.', 'success')
#     return redirect(request.referrer or url_for('index'))
#
# @app.route('/post/<int:post_id>/edit', methods=['POST'])
# @login_required
# def edit_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     if post.author != current_user:
#         abort(403)
#
#     # grab the form values
#     new_header = request.form.get('header', '').strip()
#     new_body   = request.form.get('body', '').strip()
#
#     # validate
#     if not new_header or not new_body:
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             return jsonify(success=False, error='Both title and body are required'), 400
#         flash('Both title and body are required.', 'danger')
#         return redirect(request.referrer or url_for('index'))
#
#     # apply changes
#     post.header = new_header
#     post.body   = new_body
#     db.session.commit()
#
#     # return JSON if AJAX
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return jsonify(
#             success=True,
#             post_id=post.id,
#             header=post.header,
#             body=post.body
#         )
#
#     # otherwise a normal redirect
#     flash('Your post was updated.', 'success')
#     return redirect(request.referrer or url_for('index'))
#
#
# @app.route('/post/<int:post_id>/delete', methods=['POST'])
# @login_required
# def delete_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     if post.author != current_user:
#         abort(403)
#     db.session.delete(post)
#     db.session.commit()
#     flash('Post deleted.', 'info')
#     return redirect(request.referrer or url_for('index'))
#
# @app.route('/comment/<int:comment_id>/edit', methods=['POST'])
# @login_required
# def edit_comment(comment_id):
#     c = Comment.query.get_or_404(comment_id)
#     if c.author != current_user:
#         abort(403)
#
#     # Grab the new body directly
#     new_body = request.form.get('comment_body', '').strip()
#     if not new_body:
#         return jsonify(success=False, error='Empty comment'), 400
#
#     c.body = new_body
#     db.session.commit()
#
#     # If it's an AJAX request, return JSON
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return jsonify(success=True, comment_id=c.id, body=c.body)
#
#     # Fallback (non-AJAX)
#     flash('Comment updated.', 'success')
#     return redirect(request.referrer or url_for('index'))
#
# @app.route('/comment/<int:comment_id>/delete', methods=['POST'])
# @login_required
# def delete_comment(comment_id):
#     comment = Comment.query.get_or_404(comment_id)
#     if comment.author != current_user:
#         abort(403)
#     db.session.delete(comment)
#     db.session.commit()
#     flash('Comment deleted.', 'info')
#     return redirect(request.referrer or url_for('index'))
#
# from flask import request, jsonify
#
# @app.route('/comment/<int:comment_id>/reply', methods=['POST'])
# @login_required
# def reply_comment(comment_id):
#     parent = Comment.query.get_or_404(comment_id)
#     body = request.form.get('comment_body','').strip()
#     if not body:
#         return jsonify(success=False, error='Empty reply'), 400
#
#     reply = Comment(
#         body=body,
#         author=current_user,
#         post=parent.post,
#         parent=parent
#     )
#     db.session.add(reply)
#     db.session.commit()
#
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         # return the minimal data needed to render the new reply
#         return jsonify(
#             success=True,
#             parent_id=parent.id,
#             reply_id=reply.id,
#             body=reply.body,
#             author_username=current_user.username,
#             timestamp=reply.timestamp.strftime('%b %d, %Y %H:%M')
#         )
#
#     flash('Your reply was posted.', 'success')
#     return redirect(request.referrer or url_for('index'))

# @app.route('/group/create', methods=['POST'])
# @login_required
# def create_group():
#     form = GroupForm()
#     if form.validate_on_submit():
#         new_group = Group(
#             name=form.name.data.strip(),
#             bio=form.bio.data.strip()
#         )
#         db.session.add(new_group)
#         db.session.commit()
#         # Add the creator as admin
#         gm = GroupMembers(
#             user_id=current_user.id,
#             group_id=new_group.id,
#             role='admin'
#         )
#         db.session.add(gm)
#         db.session.commit()
#         flash(f'Group "{new_group.name}" created!', 'success')
#         return redirect(url_for('group', group_id=new_group.id))
#     # If validation fails, re-display homepage with form errors
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return jsonify(success=False, errors=form.errors), 400
#     flash('Failed to create group. Please fix the errors below.', 'danger')
#     return redirect(request.referrer or url_for('index'))

#     media = request.files.get('media')
#     if media and media.filename:
#         filename = secure_filename(media.filename)
#         save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         media.save(save_path)
#         # *** assign to post.media_path ***
#         post.media_path = filename
#
#     db.session.add(post)
#     db.session.commit()
#     flash('Your post has been created!', 'success')
#     return redirect(request.referrer or url_for('index'))
#
#
# @app.route('/post/<int:post_id>/comment', methods=['POST'])
# @login_required
# def comment_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     body = request.form.get('comment_body', '').strip()
#     if not body:
#         flash('Comment cannot be empty.', 'danger')
#         return redirect(request.referrer or url_for('index'))
#     c = Comment(body=body, author=current_user, post=post)
#     db.session.add(c)
#     db.session.commit()
#     flash('Your comment was posted.', 'success')
#     return redirect(request.referrer or url_for('index'))


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Make sure the uploads directory exists
    uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    # Update the user's bio
    about_me = request.form.get('about_me', '')
    current_user.about_me = about_me

    # Handle profile picture upload
    if 'profile_picture' in request.files:
        profile_pic = request.files['profile_picture']
        if profile_pic and profile_pic.filename:
            # Make the filename unique with user ID and timestamp
            import time
            filename = f"profile_{current_user.id}_{int(time.time())}_{secure_filename(profile_pic.filename)}"
            save_path = os.path.join(uploads_dir, filename)

            # Save the file
            profile_pic.save(save_path)

            # Save the profile picture path to the user model
            current_user.profile_picture_path = filename
            print(f"Profile picture saved as: {filename}")

    # Handle banner upload
    if 'profile_banner' in request.files:
        profile_banner = request.files['profile_banner']
        if profile_banner and profile_banner.filename:
            # Make the filename unique
            import time
            filename = f"banner_{current_user.id}_{int(time.time())}_{secure_filename(profile_banner.filename)}"
            save_path = os.path.join(uploads_dir, filename)

            # Save the file
            profile_banner.save(save_path)

            # Save the banner path to the user model
            current_user.banner_path = filename
            print(f"Banner saved as: {filename}")

    # Commit changes to database
    db.session.commit()

    flash('Your profile has been updated!', 'success')
    return redirect(url_for('user', username=current_user.username))