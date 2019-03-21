import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from elasticsearch import Elasticsearch
from config import Config

#the database will be represented in the application by the database instance. The migration engine will also have an instance
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
#the function the user will be redirected to if they try to access a @loginrequired route
login.login_view = 'auth.login'
#Override the default message after a user is redirected to login page. Doing this to allow for translation
login.login_message = _l('Please log in to access this page.')
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    #to initialize it I need access to app.config, which only becomes available after the create_app() function is invoked
    #ass an elasticsearch attribute to the app instance. Elasticsearch not wrapped by flask extension
    #create an instance of class Elasticsearch to do the searching
    #make the elasticsearch attribute None if I didn't configure the env variable
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_URL'] else None

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    #add not app.testing so that all this logging is skipped during unit tests.
    #TESTING varable will be set to true when testing
    if not app.debug and not app.testing:
        # Check to see if a mail server is configured
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
                # create a SMTP handler instance which is a class from std library that logs to an email address
                mail_handler = SMTPHandler(
                    # Configure the SMTP handler object with a server and a port
                    mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                    # Give it a fake from address
                    fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                    toaddrs=app.config['ADMINS'], subject='Microblog Failure',
                    credentials=auth, secure=secure)
                # Only logs errors and not warnings
                mail_handler.setLevel(logging.ERROR)
                # attaches this to app.logger
                app.logger.addHandler(mail_handler)
            # Will create a logs directory if it doesn't exist yet
        if not os.path.exists('logs'):
            os.mkdir('logs')
            # Limits size of log file to 10KB, create a fileHandler to write logs to microblog.log
        file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
        # logging .formatter sets the format for each log line
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        # level INFO logs everything
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        # Writes this line everytime the server starts
        app.logger.info('Microblog startup')

    return app


#invoked after every request to select a language translation for that request
#Flasks .accept_languages allows you to work with the Accept-Language header the client sends with a request
@babel.localeselector
def get_locale():
    #best match gives you the language with the highest weight from the header
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])
    #return 'es'


#Prevents circular imports, all imports start from app package bc we import app from microblog which sets our cwd for
#imports at the top level
from app import models
