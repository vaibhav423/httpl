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

    return app
