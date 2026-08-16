"""Flask application factory."""
from flask import Flask
from app.config import config
from app.extensions import init_extensions, db
import os


# Placeholder values written in .env.example — detect them and warn loudly
_PLACEHOLDERS = {
    'STRIPE_SECRET_KEY':    'sk_test_replace_me',
    'STRIPE_WEBHOOK_SECRET':'whsec_replace_me',
    'STRIPE_PUBLISHABLE_KEY':'pk_test_replace_me',
}


def _warn_if_placeholder(app):
    """Log a clear warning for any config value that still holds a placeholder."""
    for key, placeholder in _PLACEHOLDERS.items():
        value = app.config.get(key, '')
        if not value or value == placeholder:
            app.logger.warning(
                f'⚠️  {key} is not set or is still the placeholder value '
                f'("{placeholder}"). Stripe checkout will return 502 until '
                f'a real test key is added to .env. '
                f'Get yours at: https://dashboard.stripe.com/test/apikeys'
            )


def create_app(config_name=None):
    """Create and configure the Flask application."""
    import os

    # __file__ is app/__init__.py → project root is one level up
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Create Flask app, pointing template and static folders at the project root
    # so templates/index.html and static/* are found even though the package
    # lives in app/.
    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'templates'),
        static_folder=os.path.join(project_root, 'static'),
        static_url_path='/static',
    )
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app.config.from_object(config[config_name])

    # ── Startup sanity checks ──────────────────────────────────────────────
    _warn_if_placeholder(app)

    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app


def register_blueprints(app):
    """Register Flask blueprints."""
    from app.routes.auth import auth_bp
    from app.routes.products import products_bp
    from app.routes.cart import cart_bp
    from app.routes.checkout import checkout_bp
    from app.routes.frontend import frontend_bp

    app.register_blueprint(frontend_bp)   # GET / — must come before API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)


def register_error_handlers(app):
    """Register error handlers.

    API routes (Accept: application/json) always get JSON errors.
    Browser navigations get a plain text 404 so they don't see raw JSON.
    """
    from flask import jsonify, request, render_template

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return '<h2 style="font-family:sans-serif;padding:40px">Page not found — ' \
               '<a href="/">Go home</a></h2>', 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403


def register_cli_commands(app):
    """Register Flask CLI commands."""
    import click
    
    @app.cli.command('init-db')
    def init_db():
        """Initialize the database."""
        db.create_all()
        click.echo('Database initialized.')
    
    @app.cli.command('seed-db')
    def seed_db():
        """Seed the database with sample data."""
        from app.seed import seed_products
        seed_products()
        click.echo('Database seeded with products.')
    
    @app.cli.command('create-admin')
    @click.option('--email', prompt=True, help='Admin email address')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
    @click.option('--name', prompt=True, help='Admin name')
    def create_admin(email, password, name):
        """Create an admin user."""
        from app.models import User
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            click.echo(f'User with email {email} already exists.')
            return
        
        user = User(name=name, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        click.echo(f'Admin user created: {email}')


# Create Celery instance for worker
def create_celery_app(app=None):
    """Create Celery app with Flask context."""
    from app.extensions import celery
    
    app = app or create_app()
    
    # Configure Celery with Flask app context
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    return celery
