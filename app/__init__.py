from flask import Flask
from app.config import get_config
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_name=None):
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'), static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    if config_name:
        app.config.from_object(get_config(config_name))
    else:
        app.config.from_object(get_config())
    from app.extensions import (
        db, migrate, csrf, mail, login_manager
    )
    
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    setup_logging(app)
    register_blueprints(app)
    register_error_handlers(app)

    @app.shell_context_processor
    def make_shell_context():
        return {'db': db}
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    with app.app_context():
        from app import models
        db.create_all()

    from app.cli import init_users
    init_users.init_app(app)

    return app
from app import models
def setup_logging(app):
    if not app.debug and not app.testing:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'app.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
        


def register_blueprints(app):
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')


def register_error_handlers(app):
    from flask import request

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f'404 error: {request.path}')
        return {'error': 'Not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        from app.extensions import db
        db.session.rollback()
        app.logger.error(f'Internal server error: {error}')
        return {'error': 'Internal server error'}, 500