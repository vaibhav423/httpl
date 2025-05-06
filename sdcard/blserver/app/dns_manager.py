import os
import subprocess
import glob
import json
import shutil

def get_global_settings():
    """Get global DNS settings"""
    settings_file = '/sdcard/blserver/conf/global_dns.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    else:
        # Default settings
        default = {
            'default_dns': '1.1.1.1',
            'global_override_enabled': False,
            'global_override_ip': '192.168.14.190'
        }
        with open(settings_file, 'w') as f:
            json.dump(default, f)
        return default

def update_global_settings(settings):
    """Update global DNS settings"""
    settings_file = '/sdcard/blserver/conf/global_dns.json'
    with open(settings_file, 'w') as f:
        json.dump(settings, f)
    
    # Update all active DNS configurations
    for user_dir in glob.glob('/sdcard/blserver/conf/users/*/'):
        user_id = os.path.basename(os.path.dirname(user_dir))
        update_user_dns(user_id)

def get_user_settings(user_id):
    """Get user-specific DNS settings"""
    settings_file = f'/sdcard/blserver/conf/users/{user_id}/settings.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    else:
        # Default user settings
        default = {
            'override_enabled': False,
            'override_ip': '',
            'custom_domains': {}  # Domain -> IP mapping
        }
        return default

def create_user_dns(user_id, ip_address):
    """Create DNS configuration for a user"""
    # Create user directory
    user_dir = f'/sdcard/blserver/conf/users/{user_id}'
    os.makedirs(user_dir, exist_ok=True)
    
    # Save IP address
    with open(f'{user_dir}/ip.txt', 'w') as f:
        f.write(ip_address)
    
    # Create default settings
    settings = get_user_settings(user_id)
    with open(f'{user_dir}/settings.json', 'w') as f:
        json.dump(settings, f)
    
    # Generate port number (10530 + user count)
    user_count = len(glob.glob('/sdcard/blserver/conf/users/*/'))
    port = 10530 + user_count - 1
    
    # Save port
    with open(f'{user_dir}/port.txt', 'w') as f:
        f.write(str(port))
    
    # Generate dnsmasq config
    update_user_dns(user_id)
    
    # Setup iptables
    setup_iptables(user_id, ip_address, port)
    
    # Start dnsmasq
    start_user_dnsmasq(user_id)
    
    return True

def update_user_dns(user_id):
    """Update DNS configuration for a user"""
    user_dir = f'/sdcard/blserver/conf/users/{user_id}'
    
    # Get user settings
    user_settings = get_user_settings(user_id)
    global_settings = get_global_settings()
    
    # Get IP and port
    with open(f'{user_dir}/ip.txt', 'r') as f:
        ip_address = f.read().strip()
    
    with open(f'{user_dir}/port.txt', 'r') as f:
        port = f.read().strip()
    
    # Create logs and pids directories with proper permissions
    logs_dir = '/sdcard/blserver/logs'
    pids_dir = '/sdcard/blserver/pids'
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(pids_dir, exist_ok=True)
    
    try:
        # Set permissions for directories
        subprocess.call(f"su -c \"chmod -R 777 {logs_dir}\"", shell=True)
        subprocess.call(f"su -c \"chmod -R 777 {pids_dir}\"", shell=True)
        subprocess.call(f"su -c \"chmod -R 777 {user_dir}\"", shell=True)
    except Exception as e:
        print(f"[WARNING] Failed to set permissions: {e}")
    
    # Generate a simplified dnsmasq config
    config = f"""port={port}
no-resolv
"""
    
    # Determine which DNS server to use as default
    if user_settings['override_enabled'] and user_settings['override_ip']:
        # User has specific override
        default_ip = user_settings['override_ip']
    elif global_settings['global_override_enabled']:
        # Global override is enabled
        default_ip = global_settings['global_override_ip']
    else:
        # Use default DNS (1.1.1.1)
        config += f"server={global_settings['default_dns']}\n"
        default_ip = None
    
    # Add default IP if set
    if default_ip:
        config += f"address=/./{default_ip}\n"
    
    # Add custom domain mappings
    for domain, ip in user_settings['custom_domains'].items():
        config += f"address=/{domain}/{ip}\n"
    
    # Write config
    with open(f'{user_dir}/dnsmasq.conf', 'w') as f:
        f.write(config)
    
    # Restart dnsmasq if it's running
    restart_user_dnsmasq(user_id)
    
    return True

def setup_iptables(user_id, ip_address, port):
    """Setup iptables rules for a user"""
    try:
        # Clear any existing rules for this IP
        cmd1 = f"su -c \"iptables -t nat -D PREROUTING -s {ip_address} -p udp --dport 53 -j REDIRECT --to-port {port}\""
        cmd2 = f"su -c \"iptables -t nat -D PREROUTING -s {ip_address} -p tcp --dport 53 -j REDIRECT --to-port {port}\""
        
        # Add new rules at the top of the chain
        cmd3 = f"su -c \"iptables -t nat -I PREROUTING -s {ip_address} -p udp --dport 53 -j REDIRECT --to-port {port}\""
        cmd4 = f"su -c \"iptables -t nat -I PREROUTING -s {ip_address} -p tcp --dport 53 -j REDIRECT --to-port {port}\""
        
        # Execute commands
        try:
            subprocess.call(cmd1, shell=True, stderr=subprocess.DEVNULL)
        except:
            pass  # Ignore errors if rule doesn't exist
            
        try:
            subprocess.call(cmd2, shell=True, stderr=subprocess.DEVNULL)
        except:
            pass  # Ignore errors if rule doesn't exist
            
        # These must succeed
        subprocess.check_call(cmd3, shell=True)
        subprocess.check_call(cmd4, shell=True)
        
        print(f"[IPTABLES] Successfully set up rules for {ip_address} to port {port}")
        
        return True
    except Exception as e:
        print(f"Error setting up iptables: {e}")
        return False

def start_user_dnsmasq(user_id):
    """Start dnsmasq for a user"""
    user_dir = f'/sdcard/blserver/conf/users/{user_id}'
    config_file = f'{user_dir}/dnsmasq.conf'
    
    try:
        # Kill any existing dnsmasq process for this user
        try:
            with open(f'{user_dir}/port.txt', 'r') as f:
                port = f.read().strip()
            cmd_kill = f"su -c \"pkill -f 'dnsmasq.*{port}'\""
            subprocess.call(cmd_kill, shell=True, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"[DNSMASQ] Error cleaning up old process: {e}")
        
        # Try a much simpler approach - just run dnsmasq directly
        cmd = f"su -c \"dnsmasq --conf-file={config_file}\""
        
        # Execute the command
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode == 0:
            print(f"[DNSMASQ] Started dnsmasq for user {user_id}")
            return True
        else:
            stderr = result.stderr.decode('utf-8')
            print(f"[DNSMASQ] Failed to start dnsmasq: {stderr}")
            
            # Try with --no-daemon to see if that helps with debugging
            cmd_debug = f"su -c \"dnsmasq --conf-file={config_file} --no-daemon\""
            print(f"[DNSMASQ] Trying with --no-daemon: {cmd_debug}")
            result_debug = subprocess.run(cmd_debug, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
            stdout = result_debug.stdout.decode('utf-8')
            stderr = result_debug.stderr.decode('utf-8')
            print(f"[DNSMASQ] Debug output: {stdout}")
            print(f"[DNSMASQ] Debug error: {stderr}")
            
            return False
        
        return True
    except Exception as e:
        print(f"Error starting dnsmasq: {e}")
        return False

def stop_user_dnsmasq(user_id):
    """Stop dnsmasq for a user"""
    pid_file = f'/sdcard/blserver/pids/dnsmasq-{user_id}.pid'
    
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = f.read().strip()
            cmd = f"su -c \"kill {pid}\""
            subprocess.call(cmd, shell=True)
            print(f"[DNSMASQ] Stopped dnsmasq for user {user_id}")
        else:
            # Try to find and kill by process name and port
            user_dir = f'/sdcard/blserver/conf/users/{user_id}'
            if os.path.exists(f'{user_dir}/port.txt'):
                with open(f'{user_dir}/port.txt', 'r') as f:
                    port = f.read().strip()
                cmd = f"su -c \"pkill -f 'dnsmasq.*{port}'\""
                subprocess.call(cmd, shell=True)
                print(f"[DNSMASQ] Attempted to stop dnsmasq for user {user_id} by port {port}")
        
        return True
    except Exception as e:
        print(f"Error stopping dnsmasq: {e}")
        return False

def restart_user_dnsmasq(user_id):
    """Restart dnsmasq for a user"""
    stop_user_dnsmasq(user_id)
    return start_user_dnsmasq(user_id)

def delete_user_dns(user_id):
    """Delete DNS configuration for a user"""
    user_dir = f'/sdcard/blserver/conf/users/{user_id}'
    
    try:
        # Get IP address and port
        with open(f'{user_dir}/ip.txt', 'r') as f:
            ip_address = f.read().strip()
        
        with open(f'{user_dir}/port.txt', 'r') as f:
            port = f.read().strip()
        
        # Stop dnsmasq
        stop_user_dnsmasq(user_id)
        
        # Remove iptables rules
        cmd1 = f"su -c \"iptables -t nat -D PREROUTING -s {ip_address} -p udp --dport 53 -j REDIRECT --to-port {port}\""
        cmd2 = f"su -c \"iptables -t nat -D PREROUTING -s {ip_address} -p tcp --dport 53 -j REDIRECT --to-port {port}\""
        
        try:
            subprocess.call(cmd1, shell=True, stderr=subprocess.DEVNULL)
            subprocess.call(cmd2, shell=True, stderr=subprocess.DEVNULL)
            print(f"[IPTABLES] Removed rules for {ip_address}")
        except Exception as e:
            print(f"[IPTABLES] Error removing rules: {e}")
        
        # Remove user directory
        shutil.rmtree(user_dir)
        
        return True
    except Exception as e:
        print(f"Error deleting user DNS: {e}")
        return False
