from app import app
import signal
import os
import sys

def signal_handler(sig, frame):
    print('Shutting down server...')
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    app.run(debug=True, host='0.0.0.0', port=5000)
