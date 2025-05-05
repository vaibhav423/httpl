from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from .models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Import routes
        from .routes import main
        
        # Register blueprints
        app.register_blueprint(main)

        # Create database tables
        db.create_all()

        # Create test user if none exists
        from .models import User
        if not User.query.first():
            test_user = User(
                mac_address="00:11:22:33:44:55",
                hostname="test-device",
                ip_address="192.168.1.100"
            )
            db.session.add(test_user)
            db.session.commit()

    return app
