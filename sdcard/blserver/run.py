#!/usr/bin/env python3
"""
DNS Controller - Main Application
--------------------------------
A Flask web application for managing DNS configurations for multiple users.
"""

import os
import sys
from app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Create necessary directories if they don't exist
    os.makedirs('/workspaces/httpl/sdcard/blserver/conf/users', exist_ok=True)
    os.makedirs('/workspaces/httpl/sdcard/blserver/logs', exist_ok=True)
    os.makedirs('/workspaces/httpl/sdcard/blserver/pids', exist_ok=True)
    
    # Get port from command line arguments or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=port, debug=True)
