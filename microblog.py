from app import create_app, db, cli
from app.models import User, Post

app = create_app()
cli.register(app)

#adds symbols that will be pre-imported when you use "flask shell"
#each item you have to also provide a name that it will be referenced in the shell, which is given by the dictionary keys.
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post}