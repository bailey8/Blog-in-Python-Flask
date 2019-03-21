from flask import jsonify, g
from app import db
from app.api import bp
from app.api.auth import basic_auth, token_auth


@bp.route('/tokens', methods=['POST'])
#tells flask-httpAuth to verify authentication through the function I defined in auth.py
@basic_auth.login_required
def get_token():
    #uses the get_token() method of the User model
    token = g.current_user.get_token()
    #writes token and it's exp date to the DB
    db.session.commit()
    return jsonify({'token': token})


@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    #uses helper method in User class
    g.current_user.revoke_token()
    db.session.commit()
    #204 is code for successful requests that have no response body
    return '', 204