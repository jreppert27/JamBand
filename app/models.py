from datetime import datetime, timezone
from hashlib import md5
from time import time
from typing import Optional, List
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login

followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))

    posts: so.WriteOnlyMapped['Post'] = so.relationship(
        back_populates='author')
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(
        back_populates='author')
    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')
    groups: so.Mapped[List['Group']] = so.relationship(
        secondary='group_members', back_populates='members')
    followed_groups: so.WriteOnlyMapped['Group'] = so.relationship(
        secondary='group_followers', back_populates='followers')
    tags: so.WriteOnlyMapped['Tag'] = so.relationship(
        secondary='tags', back_populates='users')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Post)
            .order_by(Post.timestamp.desc())
        )

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception:
            return
        return db.session.get(User, id)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    header: so.Mapped[str] = so.mapped_column(sa.String(140))
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    group_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('group.id'), index=True, nullable=True)

    author: so.Mapped[User] = so.relationship(back_populates='posts')
    group: so.Mapped[Optional['Group']] = so.relationship(back_populates='posts')
    comments: so.WriteOnlyMapped['Comment'] = so.relationship(back_populates='post')

    def __repr__(self):
        return '<Post {}>'.format(self.body)


class Comment(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    post_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Post.id), index=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    group_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('group.id'), index=True, nullable=True)

    post: so.Mapped[Post] = so.relationship(back_populates='comments')
    author: so.Mapped[User] = so.relationship(back_populates='comments')
    group: so.Mapped[Optional['Group']] = so.relationship(back_populates='comments')

    def __repr__(self):
        return '<Comment {}>'.format(self.body)


class Group(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    bio: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    posts: so.WriteOnlyMapped[Post] = so.relationship(back_populates='group')
    comments: so.WriteOnlyMapped[Comment] = so.relationship(back_populates='group')
    members: so.Mapped[List['User']] = so.relationship(
        secondary='group_members', back_populates='groups')
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary='group_followers', back_populates='followed_groups')
    tags: so.WriteOnlyMapped['Tag'] = so.relationship(
        secondary='tags',
        back_populates='groups',
        overlaps='tags')

    def __repr__(self):
        return '<Group {}>'.format(self.name)


class GroupMembers(db.Model):
    __tablename__ = 'group_members'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    group_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Group.id), index=True)
    role: so.Mapped[str] = so.mapped_column(sa.String(20), default='member')  # admin, moderator, member

    def __repr__(self):
        return '<GroupMember user_id={}, group_id={}, role={}>'.format(
            self.user_id, self.group_id, self.role)


class GroupFollowers(db.Model):
    __tablename__ = 'group_followers'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)
    group_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Group.id), index=True)
    followed_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return '<GroupFollower user_id={}, group_id={}>'.format(
            self.user_id, self.group_id)


class Tag(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(50), index=True, unique=True)
    subtag: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey('tag.id'), nullable=True)

    parent: so.Mapped[Optional['Tag']] = so.relationship('Tag', remote_side=[id], backref='children')
    users: so.WriteOnlyMapped[User] = so.relationship(
        secondary='tags',
        back_populates='tags',
        overlaps='tags')
    groups: so.WriteOnlyMapped[Group] = so.relationship(
        secondary='tags',
        back_populates='tags',
        overlaps='tags,users')

    def __repr__(self):
        return '<Tag {}>'.format(self.title)


class Tags(db.Model):
    __tablename__ = 'tags'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    group_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey(Group.id), nullable=True, index=True)
    user_id: so.Mapped[Optional[int]] = so.mapped_column(sa.ForeignKey(User.id), nullable=True, index=True)
    tag_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Tag.id), index=True)

    __table_args__ = (
        sa.CheckConstraint('(group_id IS NOT NULL) OR (user_id IS NOT NULL)',
                           name='check_group_or_user'),
    )

    def __repr__(self):
        return '<Tags group_id={}, user_id={}, tag_id={}>'.format(
            self.group_id, self.user_id, self.tag_id)