from flask import render_template
from app import db
from app.errors import bp
from flask import render_template, request
#rename to make it clear these are API errors
from app.api.errors import error_response as api_error_response

#HTTP protocol supports a way for the client and server to agree on best format for the response, called content negotiation.
def wants_json_response():
    #if JSON ranks higher than HTML then return json. Returns true to tell the error handlers to use JSON
    return request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)
def not_found_error(error):
    if wants_json_response():
        return api_error_response(404)
    #default 2nd return value is 200, want status code to reflect actual error
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(500)
    return render_template('errors/500.html'), 500