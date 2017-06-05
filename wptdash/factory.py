# -*- coding: utf-8 -*-
"""
    WPTDash
    ~~~~~~~

    An application that consolidates pull request build information into
    a single GitHub comment and provides an interface for displaying
    more detailed forms of that information.
"""

from flask import Flask, g
from wptdash.database import db
from werkzeug.utils import find_modules, import_string


def create_app(config=None):
    import wptdash.models as models

    app = Flask('wptdash')

    app.config.update(config or {})
    app.config.from_envvar('WPTDASH_SETTINGS', silent=True)

    db.init_app(app)

    @app.before_request
    def before_request():
        g.db = db
        g.models = models

    register_blueprints(app)
    register_cli(app)

    return app


def register_blueprints(app):
    """ Registers all blueprint modules. """
    for name in find_modules('wptdash.blueprints'):
        mod = import_string(name)
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp)
    return None


def register_cli(app):
    """ Registers CLI commands. """
    @app.cli.command('initdb')
    def init_db_command():
        """ Creates the database tables. """
        import wptdash.models
        db.create_all()
        print ('Initialized the database')
