from app import create_app
from app.utils import NetworkManager, IPTablesManager, DNSManager
import os
import threading
import time

app = create_app()

def scan_devices():
    """Periodically scan for connected devices"""
    while True:
        with app.app_context():
            try:
                NetworkManager.sync_connected_devices()
            except Exception as e:
                print(f"Error scanning devices: {e}")
        time.sleep(30)  # Scan every 30 seconds

if __name__ == '__main__':
    # Ensure the application instance path exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize network configuration
    with app.app_context():
        print("Initializing network configuration...")
        try:
            # Initialize iptables rules
            IPTablesManager.init_rules()
            
            # Start dnsmasq with empty config
            DNSManager.create_dnsmasq_config([])
            dns_process = DNSManager.start_dnsmasq()
            
            # Start device scanning in background
            scanner_thread = threading.Thread(target=scan_devices, daemon=True)
            scanner_thread.start()
            
            print("Network configuration initialized successfully")
        except Exception as e:
            print(f"Error initializing network: {e}")
            raise
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
