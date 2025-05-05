# app/main/routes.py
import os

from flask import render_template, flash, redirect, url_for, request, jsonify, abort, current_app, Blueprint
from flask_login import login_required, current_user
import sqlalchemy as sa                   # if you really need sa.select
from werkzeug.utils import secure_filename

from . import bp
from .. import db
from .forms import PostForm, GroupForm, FollowButton, EditProfileForm, FollowGroupForm
from ..models import *                 # and your models

# register two URLs on the same view
@bp.route('/',      methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            header=form.header.data or "New Post",
            body=form.post.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))

    # decide which posts to show
    view = request.args.get('view', 'following')
    if view == 'following':
        stmt = current_user.following_posts()
        posts = db.session.scalars(stmt).all()
    else:
        # using model’s query API is simpler:
        posts = Post.query.order_by(Post.timestamp.desc()).all()
        # OR if you really want sa.select:
        # posts = db.session.scalars(
        #     sa.select(Post).order_by(Post.timestamp.desc())
        # ).all()

    return render_template(
        'index.html',
        title='Home',
        form=form,
        posts=posts,
        view=view
    )

@bp.route('/reset_db')
def reset_db():
    flash("Resetting database and seeding with demo music-lovers data…")

    # 1) Wipe all tables
    for table in reversed(db.metadata.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()

    # 2) Create users
    alice = User(username="alice", email="alice@example.com")
    alice.set_password("password123")
    bob   = User(username="bob",   email="bob@rockrevival.org")
    bob.set_password("securepass")
    carol = User(username="carol", email="carol@indieartists.net")
    carol.set_password("mypassword")

    db.session.add_all([alice, bob, carol])
    db.session.commit()

    # 3) User-to-user follows
    alice.follow(bob)
    alice.follow(carol)
    bob.follow(alice)
    carol.follow(bob)
    db.session.commit()

    # 4) Create groups
    g1 = Group(name="Jazz Enthusiasts", bio="Discussing the smooth sounds of jazz.")
    g2 = Group(name="Rock Revival",     bio="Bringing classic rock back to life.")
    g3 = Group(name="Indie Artists",    bio="Sharing indie music and art.")
    db.session.add_all([g1, g2, g3])
    db.session.commit()

    # 5) Memberships
    db.session.add_all([
        GroupMembers(user_id=alice.id, group_id=g1.id, role="admin"),
        GroupMembers(user_id=bob.id,   group_id=g1.id, role="member"),
        GroupMembers(user_id=bob.id,   group_id=g2.id, role="admin"),
        GroupMembers(user_id=carol.id, group_id=g3.id, role="admin"),
    ])
    db.session.commit()

    # 6) Group follows
    carol.followed_groups.append(g1)
    alice.followed_groups.append(g3)
    db.session.commit()

    # 7) Seed ~25 demo posts
    demo_posts = []
    authors = [alice, bob, carol]
    groups  = [g1, g2, g3]
    for i in range(1, 26):
        author = authors[i % 3]
        if i % 5 == 0:
            # every 5th post is personal
            header = f"Personal Thought #{i}"
            body   = f"Just sharing personal reflections number {i}."
            group  = None
        else:
            grp    = groups[i % 3]
            header = f"{grp.name} Topic #{i}"
            body   = f"Discussion point {i} in {grp.name}. What do you think?"
            group  = grp

        demo_posts.append(Post(
            header=header,
            body=body,
            author=author,
            group=group
        ))

    db.session.add_all(demo_posts)
    db.session.commit()

    # 8) Seed a few comments & replies
    c1 = Comment(body="Absolutely a masterpiece!", author=bob,   post=demo_posts[0])
    c2 = Comment(body="I'll give it a listen tonight.",   author=carol, post=demo_posts[0], parent=c1)
    c3 = Comment(body="Congrats on the EP launch!",      author=alice, post=demo_posts[2])
    c4 = Comment(body="I love jazz piano too—check out Bill Evans.", author=carol, post=demo_posts[3])
    db.session.add_all([c1, c2, c3, c4])
    db.session.commit()

    return redirect(url_for('main.index'))


@bp.route('/group/create', methods=['POST'])
@login_required
def create_group():
    form = GroupForm()
    if form.validate_on_submit():
        new_group = Group(
            name=form.name.data.strip(),
            bio=form.bio.data.strip()
        )
        db.session.add(new_group)
        db.session.commit()
        # Add the creator as admin
        gm = GroupMembers(
            user_id=current_user.id,
            group_id=new_group.id,
            role='admin'
        )
        db.session.add(gm)
        db.session.commit()
        flash(f'Group "{new_group.name}" created!', 'success')
        return redirect(url_for('main.group', group_id=new_group.id))
    # If validation fails, re-display homepage with form errors
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=False, errors=form.errors), 400
    flash('Failed to create group. Please fix the errors below.', 'danger')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/create_post', methods=['POST'])
@login_required
def create_post():
    header = request.form.get('header','').strip()
    body   = request.form.get('body','').strip()
    if not header or not body:
        flash('Title and text are required.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    post = Post(header=header, body=body, author=current_user)

    media = request.files.get('media')
    if media and media.filename:
        filename = secure_filename(media.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        media.save(os.path.join(upload_folder, filename))
        post.media_path = filename

    group_id = request.form.get('group_id').strip()
    if group_id:
        try:
            post.group_id = int(group_id)
        except ValueError:
            pass

    db.session.add(post)
    db.session.commit()
    flash('Your post has been created!', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user_obj = User.query.filter_by(username=username).first_or_404()

    # 1) Follow/unfollow form, only for non-owners
    follow_form = FollowButton()
    is_following = current_user.is_following(user_obj)
    if user_obj != current_user and follow_form.validate_on_submit():
        if is_following:
            current_user.unfollow(user_obj)
            flash(f'You have unfollowed {user_obj.username}.', 'info')
        else:
            current_user.follow(user_obj)
            flash(f'You are now following {user_obj.username}.', 'success')
        db.session.commit()
        return redirect(url_for('main.user', username=username))

    # 2) Edit-profile form, only for the owner
    edit_form = EditProfileForm()
    if user_obj == current_user and edit_form.validate_on_submit():
        # update bio
        current_user.about_me = edit_form.about_me.data

        # handle profile picture
        pic = edit_form.profile_picture.data
        if pic:
            filename = secure_filename(pic.filename)
            pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            current_user.profile_picture_path = filename

        # handle banner
        banner = edit_form.profile_banner.data
        if banner:
            fname = secure_filename(banner.filename)
            banner.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname))
            current_user.banner_path = fname

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('main.user', username=username))

    # render
    return render_template(
        'profile.html',
        title=f"{user_obj.username}'s Profile",
        user=user_obj,
        groups=user_obj.groups,
        follow_form=follow_form,
        is_following=is_following,
        edit_profile_form=edit_form
    )

    groups = user_obj.groups
    return render_template(
        'profile.html',
        title=f"{user_obj.username}'s Profile",
        user=user_obj,
        groups=groups,
        form=form,
        is_following=is_following
    )

@bp.route('/group/<int:group_id>')
@login_required
def group(group_id):
    group_obj = db.session.get(Group, group_id) or abort(404)

    # figure out your membership and role
    membership = current_user.get_membership(group_id)
    is_member = membership is not None
    is_admin  = is_member and membership.role == 'admin'

    members = group_obj.members   # list of User

    return render_template('group.html',
        title=group_obj.name,
        group=group_obj,
        members=members,
        is_member=is_member,
        is_admin=is_admin
    )

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    body = request.form.get('comment_body','').strip()
    if not body:
        flash('Comment cannot be empty.', 'danger')
        return redirect(request.referrer or url_for('main.index'))
    c = Comment(body=body, author=current_user, post=post)
    db.session.add(c)
    db.session.commit()
    flash('Your comment was posted.', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/post/<int:post_id>/edit', methods=['GET','POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        abort(403)
    form = PostForm(obj=post)

    if request.method == 'GET':
        # return ONLY the form fragment
        return render_template(
            'partials/_edit_post_form.html',
            form=form,
            post=post
        )

    # POST…
    if form.validate_on_submit():
        post.header = form.header.data
        post.body   = form.body.data
        db.session.commit()
        # return updated data for JS to re-draw
        return jsonify(
            success=True,
            header=post.header,
            body=post.body
        )

    # validation failed
    return jsonify(success=False, errors=form.errors), 400

@bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/comment/<int:comment_id>/edit', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user:
        abort(403)

    new_body = request.form.get('comment_body', '').strip()
    if not new_body:
        if request.is_xhr:
            return jsonify(success=False, error="Comment body can’t be empty"), 400
        flash("Comment body can’t be empty", "danger")
        return redirect(request.referrer or url_for('main.index'))

    comment.body = new_body
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(
            success=True,
            comment_id=comment.id,
            body=new_body
        )

    flash("Comment updated", "success")
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(request.referrer or url_for('main.index'))

from flask import request, jsonify

@bp.route('/comment/<int:comment_id>/reply', methods=['POST'])
@login_required
def reply_comment(comment_id):
    parent = Comment.query.get_or_404(comment_id)
    body = request.form.get('comment_body','').strip()
    if not body:
        return jsonify(success=False, error='Empty reply'), 400

    reply = Comment(
        body=body,
        author=current_user,
        post=parent.post,
        parent=parent
    )
    db.session.add(reply)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # return the minimal data needed to render the new reply
        return jsonify(
            success=True,
            parent_id=parent.id,
            reply_id=reply.id,
            body=reply.body,
            author_username=current_user.username,
            timestamp=reply.timestamp.strftime('%b %d, %Y %H:%M')
        )

    flash('Your reply was posted.', 'success')
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def create_comment(post_id):
    post = Post.query.get_or_404(post_id)
    body = request.form.get('comment_body','').strip()
    parent_id = request.form.get('parent_id')

    if not body:
        return jsonify(success=False, error="Comment cannot be empty."), 400

    comment = Comment(
        body=body,
        author=current_user,
        post=post,
        parent_id=int(parent_id) if parent_id else None
    )
    db.session.add(comment)
    db.session.commit()

    # If AJAX, return JSON so your JS can insert the new comment inline
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(
            success=True,
            comment_id=comment.id,
            parent_id=comment.parent_id,
            body=comment.body,
            author_username=current_user.username,
            timestamp=comment.timestamp.strftime('%b %d, %Y %H:%M')
        )

    flash("Your comment was posted!", "success")
    # return redirect(request.referrer or url_for('main.index'))


@bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        # handle profile picture upload
        pic = form.profile_picture.data
        if pic:
            filename = secure_filename(pic.filename)
            pic.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    # Make sure the uploads directory exists
    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
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

        # handle banner upload
        banner = form.profile_banner.data
        if banner:
            banner_filename = secure_filename(banner.filename)
            banner.save(os.path.join(current_app.config['UPLOAD_FOLDER'], banner_filename))
            current_user.banner_path = banner_filename

        # about me
        current_user.about_me = form.about_me.data

        db.session.commit()
        flash('Your profile has been updated.', 'success')
    else:
        flash('Error updating profile. Please check the fields.', 'danger')

    return redirect(url_for('main.user', username=current_user.username))


@bp.route('/group/<int:group_id>/update', methods=['POST'])
@login_required
def update_group(group_id):
    # Get the group and verify current user is a member
    group = Group.query.get_or_404(group_id)

    # Check if user is a member of this group
    is_member = current_user in group.members
    if not is_member:
        flash('You must be a member of this group to edit it.', 'danger')
        return redirect(url_for('main.group', group_id=group_id))

    # Make sure the uploads directory exists
    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)

    # Update the group's bio
    bio = request.form.get('bio', '')
    group.bio = bio

    # Handle group avatar upload
    if 'group_avatar' in request.files:
        avatar = request.files['group_avatar']
        if avatar and avatar.filename:
            # Make the filename unique with group ID and timestamp
            import time
            filename = f"group_avatar_{group_id}_{int(time.time())}_{secure_filename(avatar.filename)}"
            save_path = os.path.join(uploads_dir, filename)

            # Save the file
            avatar.save(save_path)

            # Save the avatar path to the group model
            group.avatar_path = filename
            print(f"Group avatar saved as: {filename}")

    # Handle group banner upload
    if 'group_banner' in request.files:
        banner = request.files['group_banner']
        if banner and banner.filename:
            # Make the filename unique
            import time
            filename = f"group_banner_{group_id}_{int(time.time())}_{secure_filename(banner.filename)}"
            save_path = os.path.join(uploads_dir, filename)

            # Save the file
            banner.save(save_path)

            # Save the banner path to the group model
            group.banner_path = filename
            print(f"Group banner saved as: {filename}")

    # Commit changes to database
    db.session.commit()

    flash('Group has been updated!', 'success')
    return redirect(url_for('main.group', group_id=group_id))

@bp.route('/group/<int:group_id>/follow')
@login_required
def follow_group(group_id):
    g = db.session.get(Group, group_id) or abort(404)
    if current_user not in g.followers:
        g.followers.append(current_user)
        db.session.commit()
        flash(f'You are now following {g.name}.', 'success')
    return redirect(url_for('main.group', group_id=group_id))

@bp.route('/group/<int:group_id>/unfollow')
@login_required
def unfollow_group(group_id):
    g = db.session.get(Group, group_id) or abort(404)
    if current_user in g.followers:
        g.followers.remove(current_user)
        db.session.commit()
        flash(f'You have unfollowed {g.name}.', 'info')
    return redirect(url_for('main.group', group_id=group_id))

@bp.route('/group/<int:group_id>/leave')
@login_required
def leave_group(group_id):
    gm = GroupMembers.query.filter_by(
        group_id=group_id,
        user_id=current_user.id
    ).first()
    if gm:
        db.session.delete(gm)
        db.session.commit()
        flash('You have left the group.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/group/<int:group_id>/add_member')
@login_required
def add_member(group_id):
    group = db.session.get(Group, group_id) or abort(404)
    membership = current_user.get_membership(group_id)
    if not membership or membership.role != 'admin':
        abort(403)

    username = request.args.get('username','').strip()
    if username:
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('User not found.', 'warning')
        else:
            exists = GroupMembers.query.filter_by(
                group_id=group_id,
                user_id=user.id
            ).first()
            if not exists:
                gm = GroupMembers(user_id=user.id,
                                  group_id=group_id,
                                  role='member')
                db.session.add(gm)
                db.session.commit()
                flash(f'{user.username} added to "{group.name}".', 'success')
            else:
                flash(f'{user.username} is already a member.', 'info')
    else:
        flash('Please enter a username.', 'warning')

    return redirect(url_for('main.group', group_id=group_id))

@bp.route('/group/<int:group_id>/remove_member/<int:user_id>')
@login_required
def remove_member(group_id, user_id):
    group = db.session.get(Group, group_id) or abort(404)
    membership = current_user.get_membership(group_id)
    if not membership or membership.role != 'admin':
        abort(403)

    if user_id == current_user.id:
        flash('Admins cannot remove themselves — use Leave Group.', 'warning')
    else:
        gm = GroupMembers.query.filter_by(
            group_id=group_id, user_id=user_id
        ).first()
        if gm:
            db.session.delete(gm)
            db.session.commit()
            flash('Member removed.', 'info')

    return redirect(url_for('main.group', group_id=group_id))