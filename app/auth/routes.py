from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user
from flask_babel import _
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, \
    ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from app.auth.email import send_password_reset_email


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        #Do another set of validation server side
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        #Checks to make sure a full URL isn't injected into the next arg to redirect to maliciuous site
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title=_('Sign In'), form=form)



@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title=_('Register'), form=form)



@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    #If they are authenticated/logged in then there is no need to reset the pass
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    #Send user a form to enter which email they want the verification to be sent to
    form = ResetPasswordRequestForm()
    #Check to see if there actually is a user with the email listed in the form
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            #send the email if everything was successful, using the
            send_password_reset_email(user)
        #Flash this msg no matter what, so users can't use this to check if someone else is using the site
        flash(_('Check your email for the instructions to reset your password'))
        return redirect(url_for('auth.login'))
    #The first request to this route will just load the form where user enters their email
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)


#When the user clicks the email sent to them, this route is triggered. This link is made in the reset_password.html
@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    #Verify which user clicked on the link by using the static method attached to User
    user = User.verify_reset_password_token(token)
    #None is returned if the token is invalid
    if not user:
        return redirect(url_for('main.index'))
    #If it's valid then give the user a form to actually change their password
    form = ResetPasswordForm()
    if form.validate_on_submit():
        #if form is valid use the set_password method to update the user's password
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)