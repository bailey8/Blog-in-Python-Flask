import base64
from datetime import datetime, timedelta
from time import time
from flask import current_app, url_for
from flask_login import UserMixin
import os
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login
from app.search import add_to_index, remove_from_index, query_index
from random import randint
from flask_login import current_user


class SearchableMixin(object):
    #wraps the query_index() function in app/search.py
    @classmethod
    def search(cls, expression, page, per_page):
        #query the index of the models tablename
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        #list of tuples (search query id,index)
        for i in range(len(ids)):
            when.append((ids[i], i))
        #retrieves the list of objects by their IDs, based on a CASE statement from SQL,
        #needs to be used to ensure that the results from the database come in the same order as the IDs are given.
        # This is important because the Elasticsearch query returns results sorted from more to less relevant.
        return cls.query.filter(cls.id.in_(ids)).order_by(db.case(when, value=cls.id)), total

    @classmethod
    #before_commit is an event from sql_alchemy
    def before_commit(cls, session):
        #after commit these objects won't be available, so save them in dict and use to update elasticsearch
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            #Add each record if it belongs to a class that inherits SearchableMixin
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        #adds all posts in db to search index
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

#call beofre_commit and after_commit before and after each commit
db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class PaginatedAPIMixin(object):
    @staticmethod
    #produces a dictionary with the user collection representation
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        #take the query and add pagnation to it, returns empty list if page doesn't exist
        resources = query.paginate(page, per_page, False)
        data = {
            #get the actual items from the query. Trying to make a generic function, so it will call to_dict()
            #on each item to get it's representation for whatever type it is
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                #since many routes have arguments I need to capture additional kwargs
                'self': url_for(endpoint, page=page, per_page=per_page,**kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page, **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page, **kwargs) if resources.has_prev else None
            }
        }
        return data


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, PaginatedAPIMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    #I'll need to search the db by the token, so make it indexed
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    #called whenever a user is created/user requests pass change to hash whatever password they give
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size,username = None):
        if username == "Jordan":
            return f"/static/J{size}.jpeg"
        if randint(1, 2) == 1:
                return f"/static/python{size}.jpg"
        return f"/static/flask{size}.png"

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    #called in email.py to generate a token that is sent with the email
    def get_reset_password_token(self, expires_in=600):
        #the .decode is needed because the .encode() returns the token as a byte sequence, but we want a string
        return jwt.encode(
            #put the user's id in the payload that matched the email sent in the first reset_pass form
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    #Static methods can be called directly on the class, like cls methods but don't receive cls as first arg
    @staticmethod
    def verify_reset_password_token(token):
        #If token can't be validated or the token is expired, then return None to caller
        try:
            #return the id if the token is valid
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        #If token is valid get the user matching the payload and load the user
        return User.query.get(id)

    #used to get a representation of each user for the API
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'about_me': self.about_me,
            'post_count': self.posts.count(),
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followed', id=self.id),
                #same avatar method used to render avatars in the web pages
                'avatar': self.avatar(140)
            }
        }
        #only include email when user requests their own data
        if include_email:
            data['email'] = self.email
        return data

    #the client passes a user representation in a request and the server needs to parse it and convert it to a User object
    def from_dict(self, data, new_user=False):
        #for now only check for these 3 attributes
        for field in ['username', 'email', 'about_me']:
            if field in data:
                #set the new value in the corresponding attribute for the object.
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        #returns current token if a current token exists and has > 60 seconds left
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        #encoded in base64 so all characters are readable
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        #used to remove token, sets the exp date to 1 second
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        #if user is not found or token is expired
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user



class Post(SearchableMixin, db.Model):
    # this __searchable__ attribute is just a variable, it does not have any behavior associated with it
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        return '<Post {}>'.format(self.body)
    #



@login.user_loader
def load_user(id):
    #convert to int so we can use it in a query in the db
    return User.query.get(int(id))
