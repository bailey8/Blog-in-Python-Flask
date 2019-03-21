import os
from dotenv import load_dotenv
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret'
    #the location of the applications database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    #Signals to the application every time a change is about to be made to the database
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    #The recipients of the email
    ADMINS = ['jordantestcs@gmail.com']
    POSTS_PER_PAGE = 3
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LANGUAGES = ['en', 'es']

#When usign my own email
# set MAIL_SERVER=smtp.googlemail.com
# set MAIL_PORT=587
# set MAIL_USERNAME=jordantestcs@gmail.com
# set MAIL_PASSWORD=100679Vcs
# set MAIL_USE_TLS=1


#When using a fake python mail server
# set MAIL_SERVER=localhost
# set MAIL_PORT=8025
# This server doesn't require credentials or encryption so the variables below are optional
# set MAIL_USE_TLS=1
# set MAIL_USERNAME=<your-gmail-username>
# set MAIL_PASSWORD=<your-gmail-password>
#MAKE SURE NOT RUNNING IN DEBUG MODE

#bb0d9369dcc943e6bfe0fc0a65c75924