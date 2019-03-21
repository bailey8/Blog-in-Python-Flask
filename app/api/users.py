from flask import jsonify, request, url_for, g, abort
from app import db
from app.models import User
from app.api import bp
from app.api.auth import token_auth
from app.api.errors import bad_request

#return a user
@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    #if the user exists, return its's representation
    return jsonify(User.query.get_or_404(int(id)).to_dict())

#return a collection of users
@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)

#return followers of a user
@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    #page 1 will be default
    page = request.args.get('page', 1, type=int)
    #take whichever one is smaller, don't let user pick something over 100
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
                                   'api.get_followers', id=id)
    return jsonify(data)

#return users the user is following
@bp.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,'api.get_followed', id=id)
    return jsonify(data)

#register a new account. no login required because a new user won't have an account
@bp.route('/users', methods=['POST'])
def create_user():
    #request.get_json() returns None if there isn't JSON
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        #bad_request is a 400 error defined in errors.py
        return bad_request('must include username, email and password fields')
    #check to make sure username isn't taken
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    #check to make sure email isn't taken
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    #give the user values based of the JSON after it's confirmed as valid
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response

#modify a user
@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    #return 403 error response if user tries to change someone elses ID
    if g.current_user.id != id:
        abort(403)
    #load user, or return 404 if not found
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    #make sure username/password isn't taken, check to make sure username/pass is in the json
    if 'username' in data and data['username'] != user.username and \
            User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
            User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    #new_user is false indicating there's no password to be set
    user.from_dict(data, new_user=False)
    db.session.commit()
    #return the new user that was just created to the client
    return jsonify(user.to_dict())