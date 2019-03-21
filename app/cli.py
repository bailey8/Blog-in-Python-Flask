import os
import click


#these commands are registered at start up, not during the handling of a request, which is the only time when current_app can be used
def register(app):
    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass

    # the docstrings for these functions are used as help message in the --help output.
    # Click passes the value provided in the command to the handler function as an argument,
    @translate.command()
    @click.argument('lang')
    def init(lang):
        """Initialize a new language."""
        if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system(
                'pybabel init -i messages.pot -d app/translations -l ' + lang):
            raise RuntimeError('init command failed')
        os.remove('messages.pot')

    # run the functions and make sure that the return value is zero, which implies that the command did not return any error.
    @translate.command()
    def update():
        """Update all languages."""
        if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system('pybabel update -i messages.pot -d app/translations'):
            raise RuntimeError('update command failed')
        os.remove('messages.pot')

    @translate.command()
    def compile():
        """Compile all languages."""
        if os.system('pybabel compile -d app/translations'):
            raise RuntimeError('compile command failed')