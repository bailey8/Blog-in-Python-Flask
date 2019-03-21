from flask import Blueprint

bp = Blueprint('auth', __name__)

#routes import forms, so just import routes
from app.auth import routes