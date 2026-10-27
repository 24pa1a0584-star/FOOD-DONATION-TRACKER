import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from models import db, User

load_dotenv()

IST = timezone(timedelta(hours=5, minutes=30))

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-food-donation-tracker-2026'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    # Render uses PostgreSQL; explicitly select the installed psycopg 3 driver.
    database_url = app.config['SQLALCHEMY_DATABASE_URI']
    for prefix in ('postgres://', 'postgresql://'):
        if database_url.startswith(prefix):
            database_url = 'postgresql+psycopg://' + database_url[len(prefix):]
            break
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
    app.config['SHOW_DEMO_ACCOUNTS'] = os.environ.get('SHOW_DEMO_ACCOUNTS') == 'true'

    if os.environ.get('RENDER') == 'true' and not app.testing:
        secret = app.config['SECRET_KEY']
        if not secret or len(secret) < 32 or secret.startswith(('dev-secret-', 'change-this-')):
            raise RuntimeError('Set SECRET_KEY to a random value of at least 32 characters on Render.')
        if not database_url.startswith('postgresql+psycopg://'):
            raise RuntimeError('Set DATABASE_URL to your Render PostgreSQL connection string.')
        app.config.update(SESSION_COOKIE_SECURE=True, REMEMBER_COOKIE_SECURE=True)
    app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

    # Initialize extensions
    db.init_app(app)
    csrf = CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Jinja2 custom filters for IST time formatting
    @app.template_filter('to_ist')
    def to_ist_filter(dt, format='%d %b %Y, %I:%M %p'):
        if not dt:
            return ''
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ist_dt = dt.astimezone(IST)
        return ist_dt.strftime(format)

    @app.template_filter('to_iso')
    def to_iso_filter(dt):
        if not dt:
            return ''
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    # Register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.donations import donations_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(donations_bp)
    app.register_blueprint(api_bp)

    @app.get('/healthz')
    def health():
        try:
            db.session.execute(text('SELECT 1'))
        except SQLAlchemyError:
            db.session.rollback()
            return {'status': 'unavailable'}, 503
        return {'status': 'ok'}, 200

    # Custom Error Pages
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Auto create tables if running app
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
