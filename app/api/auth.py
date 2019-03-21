from flask import g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from flask_login import current_user
from app.models import User
from app.api.errors import error_response

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

#This is called first, user needs to log in before they can request token
@basic_auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return False
    #save this as a global variable to access in API view functions
    g.current_user = user
    #returns true or false
    return user.check_password(password)

#if credentials aren't valid during the verify_password function, return an unauthorized error
@basic_auth.error_handler
def basic_auth_error():
    return error_response(401)

#to verify authentication, Flask-HTTPAuth uses a verify_token decorator
@token_auth.verify_token
def verify_token(token):
    #locate user with provided token. If it doesn't exist return None
    g.current_user = User.check_token(token) if token else None
    #will be true or false
    return g.current_user is not None


@token_auth.error_handler
def token_auth_error():
    return error_response(401)