import os
from flask import Flask
from flask_login import LoginManager
from config import config
from models import db, User, Category, Post, Tag

login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'warning'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Custom Jinja filters
    @app.template_filter('datetimeformat')
    def datetimeformat(value, format='%b %d, %Y'):
        if value is None:
            return ''
        return value.strftime(format)

    @app.template_filter('nl2br')
    def nl2br(value):
        if not value:
            return ''
        lines = value.split('\n')
        return '<br>'.join(lines)

    # CLI Command to initialize DB and seed initial sample data
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize database tables and seed default categories."""
        db.create_all()
        seed_default_data()
        print("Database initialized and seeded successfully.")

    # Automatically create tables and seed default categories if database is fresh
    with app.app_context():
        db.create_all()
        seed_default_data()

    return app


def seed_default_data():
    """Seed initial categories and an admin user if database is empty."""
    default_categories = [
        'Technology',
        'Web Development',
        'Design',
        'Programming',
        'Tutorials'
    ]
    for cat_name in default_categories:
        slug = Category.generate_slug(cat_name)
        if not Category.query.filter_by(slug=slug).first():
            db.session.add(Category(name=cat_name, slug=slug))
    db.session.commit()


app = create_app(os.getenv('FLASK_CONFIG', 'default'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
