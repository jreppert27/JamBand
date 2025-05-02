# app/main/routes.py
import os

from flask import render_template, flash, redirect, url_for, request, jsonify, abort, current_app, Blueprint
from flask_login import login_required, current_user
import sqlalchemy as sa                   # if you really need sa.select
from werkzeug.utils import secure_filename

from . import bp
from app import db
from .forms import PostForm, GroupForm, FollowButton, EditProfileForm
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
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()

    # 2) Create some realistic users
    alice = User(username="alice", email="alice@example.com")
    alice.set_password("password123")
    bob   = User(username="bob",   email="bob@rockrevival.org")
    bob.set_password("securepass")
    carol = User(username="carol", email="carol@indieartists.net")
    carol.set_password("mypassword")

    db.session.add_all([alice, bob, carol])
    db.session.commit()

    # 3) Follow relationships
    alice.follow(bob)    # Alice follows Bob
    alice.follow(carol)  # Alice follows Carol
    bob.follow(alice)    # Bob follows Alice
    carol.follow(bob)    # Carol follows Bob
    db.session.commit()

    # 4) Create some music-themed groups
    g1 = Group(name="Jazz Enthusiasts", bio="Discussing the smooth sounds of jazz.")
    g2 = Group(name="Rock Revival",     bio="Bringing classic rock back to life.")
    g3 = Group(name="Indie Artists",    bio="Sharing indie music and art.")

    db.session.add_all([g1, g2, g3])
    db.session.commit()

    # 5) Assign members & admins in groups
    gm1 = GroupMembers(user_id=alice.id, group_id=g1.id, role="admin")
    gm2 = GroupMembers(user_id=bob.id,   group_id=g1.id, role="member")
    gm3 = GroupMembers(user_id=bob.id,   group_id=g2.id, role="admin")
    gm4 = GroupMembers(user_id=carol.id, group_id=g3.id, role="admin")

    db.session.add_all([gm1, gm2, gm3, gm4])
    db.session.commit()

    # 6) Group followers
    gf1 = GroupFollowers(user_id=carol.id, group_id=g1.id)  # Carol follows Jazz Enthusiasts
    gf2 = GroupFollowers(user_id=alice.id, group_id=g3.id)  # Alice follows Indie Artists

    db.session.add_all([gf1, gf2])
    db.session.commit()

    # 7) Create a mix of personal & group posts
    p1 = Post(
        header="Exploring Miles Davis",
        body="Anyone listened to 'Kind of Blue'? Thoughts?",
        author=alice, group=g1
    )
    p2 = Post(
        header="Rock Cover Release",
        body="Just dropped my cover of 'Stairway to Heaven'—feedback welcome!",
        author=bob, group=g2
    )
    p3 = Post(
        header="EP Launch",
        body="My debut indie EP is out now on all streaming platforms!",
        author=carol, group=g3
    )
    p4 = Post(
        header="Random Thought",
        body="Does anyone here play the piano? I'm looking for tips!",
        author=alice
    )
    p5 = Post(
        header="Live Jazz This Weekend",
        body="Downtown club hosting a live set—who's in?",
        author=bob, group=g1
    )

    db.session.add_all([p1, p2, p3, p4, p5])
    db.session.commit()

    # 8) Seed some comments & nested replies
    c1 = Comment(body="Absolutely a masterpiece!", author=bob,   post=p1)
    c2 = Comment(body="I'll give it a listen tonight.",   author=carol, post=p1, parent=c1)
    c3 = Comment(body="Congrats on the EP launch!",      author=alice, post=p3)
    c4 = Comment(body="I love jazz piano too—check out Bill Evans.", author=carol, post=p4)

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
    members = group_obj.members  # assumes this relationship is now readable
    return render_template(
        'group.html',
        title=group_obj.name,
        group=group_obj,
        members=members
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

@bp.route('/post/<int:post_id>/edit', methods=['POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)

    # grab the form values
    new_header = request.form.get('header', '').strip()
    new_body   = request.form.get('body', '').strip()

    # validate
    if not new_header or not new_body:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, error='Both title and body are required'), 400
        flash('Both title and body are required.', 'danger')
        return redirect(request.referrer or url_for('main.index'))

    # apply changes
    post.header = new_header
    post.body   = new_body
    db.session.commit()

    # return JSON if AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(
            success=True,
            post_id=post.id,
            header=post.header,
            body=post.body
        )

    # otherwise a normal redirect
    flash('Your post was updated.', 'success')
    return redirect(request.referrer or url_for('main.index'))


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