from app import create_app
from app.models import User
import os

app = create_app()

if __name__ == '__main__':
    # Ensure the application instance path exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Create a test user if none exists
    with app.app_context():
        if not User.query.first():
            from app.models import db
            test_user = User(
                mac_address="00:11:22:33:44:55",
                hostname="test-device",
                ip_address="192.168.1.100"
            )
            db.session.add(test_user)
            db.session.commit()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
