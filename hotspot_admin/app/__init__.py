from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config
from .models import db, AdminUser, User, BlockedSite

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    with app.app_context():
        # Import routes
        from .routes import main, auth
        
        # Register blueprints
        app.register_blueprint(main)
        app.register_blueprint(auth)

        # Create database tables
        db.create_all()

        # Create default admin user if none exists
        if not AdminUser.query.filter_by(username='admin').first():
            admin = AdminUser(
                username='admin',
                password_hash='pbkdf2:sha256:150000$lQEpqG8y$dd95d32c9a75847997a998a5feeding7384787822451972509512a0157dbf83ed6'  # password: admin
            )
            db.session.add(admin)
            db.session.commit()

    return app

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))
