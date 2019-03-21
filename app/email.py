from threading import Thread
from flask import current_app
from flask_mail import Message
from app import mail



#create a new background thread for the email being sent
#have to manually create application context for custom threads
def send_async_email(app, msg):
    #mail.send() needs to access the configuration values for the email server, and that can only be done by knowing where application is
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    #This allows sending the email to run in the background, and once process is over the the thread will end
    #extracts the actual application instance from inside the proxy object
    Thread(target=send_async_email,args=(current_app._get_current_object(), msg)).start()