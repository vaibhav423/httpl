from app import create_app
from app.utils import NetworkManager, IPTablesManager, DNSManager
import os
import threading
import time
import signal
import sys

app = create_app()
dns_process = None

def format_init_commands():
    """Format initialization commands with proper interface names and subnet"""
    commands = []
    for cmd in app.config['INIT_COMMANDS']:
        commands.append(cmd.format(
            iface=app.config['HOTSPOT_INTERFACE'],
            subnet=app.config['HOTSPOT_SUBNET'],
            wan_iface=app.config['WAN_INTERFACE']
        ))
    return commands

def scan_devices():
    """Periodically scan for connected devices"""
    while True:
        with app.app_context():
            try:
                NetworkManager.sync_connected_devices()
            except Exception as e:
                print(f"Error scanning devices: {e}")
        time.sleep(app.config['DEVICE_SCAN_INTERVAL'])

def cleanup(signum=None, frame=None):
    """Cleanup on exit"""
    print("\nCleaning up...")
    try:
        # Stop dnsmasq
        if dns_process:
            dns_process.terminate()
            dns_process.wait(timeout=5)
        DNSManager.stop_dnsmasq()
        
        # Clear iptables rules
        IPTablesManager.clear_rules()
        
        # Remove temporary files
        for path in [
            app.config['DNSMASQ_CONF_PATH'],
            app.config['DNSMASQ_PID_PATH'],
            app.config['DNSMASQ_LOG_PATH'],
            app.config['DNSMASQ_LEASE_PATH']
        ]:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except:
                pass
    except:
        pass
    
    sys.exit(0)

if __name__ == '__main__':
    # Register cleanup handler
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    # Ensure the application instance path exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize network configuration
    with app.app_context():
        print("Initializing network configuration...")
        try:
            # Update initialization commands with current interface
            app.config['INIT_COMMANDS'] = format_init_commands()
            
            # Initialize iptables rules
            IPTablesManager.init_rules()
            
            # Start dnsmasq with empty config
            DNSManager.create_dnsmasq_config([])
            dns_process = DNSManager.start_dnsmasq()
            
            # Start device scanning in background
            scanner_thread = threading.Thread(target=scan_devices, daemon=True)
            scanner_thread.start()
            
            print(f"Network configuration initialized successfully on {app.config['HOTSPOT_INTERFACE']}")
            print(f"Hotspot IP: {app.config['HOTSPOT_IP']}")
            print(f"DHCP Range: {app.config['DHCP_RANGE_START']} - {app.config['DHCP_RANGE_END']}")
        except Exception as e:
            print(f"Error initializing network: {e}")
            cleanup()
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    finally:
        cleanup()
