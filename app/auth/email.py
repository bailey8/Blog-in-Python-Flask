from flask import render_template, current_app
from flask_babel import _
from app.email import send_email


#This function is called when a user requests a new email and successfuly enters a valid email into the first password form
def send_password_reset_email(user):
    #Get a token with a payload that matches the user that requested the request
    token = user.get_reset_password_token()
    send_email(_('[Microblog] Reset Your Password'),
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt', user=user, token=token),
               html_body=render_template('email/reset_password.html', user=user, token=token))