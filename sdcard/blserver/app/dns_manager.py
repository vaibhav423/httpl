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
    
    # Generate dnsmasq config
    config = f"""port={port}
no-resolv
log-facility=/sdcard/blserver/logs/dnsmasq-{user_id}.log
pid-file=/sdcard/blserver/pids/dnsmasq-{user_id}.pid
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
    pid_file = f'/sdcard/blserver/pids/dnsmasq-{user_id}.pid'
    log_file = f'/sdcard/blserver/logs/dnsmasq-{user_id}.log'
    
    try:
        # Make sure the directories exist
        os.makedirs(os.path.dirname(pid_file), exist_ok=True)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Set proper permissions for directories
        subprocess.call(f"su -c \"chmod 777 {os.path.dirname(pid_file)}\"", shell=True)
        subprocess.call(f"su -c \"chmod 777 {os.path.dirname(log_file)}\"", shell=True)
        
        # Kill any existing dnsmasq process for this user
        try:
            with open(f'{user_dir}/port.txt', 'r') as f:
                port = f.read().strip()
            cmd_kill = f"su -c \"pkill -f 'dnsmasq.*{port}'\""
            subprocess.call(cmd_kill, shell=True, stderr=subprocess.DEVNULL)
            # Also try to kill by PID if the file exists
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = f.read().strip()
                    if pid:
                        subprocess.call(f"su -c \"kill {pid}\"", shell=True, stderr=subprocess.DEVNULL)
                # Remove the old PID file
                os.remove(pid_file)
        except Exception as e:
            print(f"[DNSMASQ] Error cleaning up old process: {e}")
        
        # First, test the configuration
        test_cmd = f"su -c \"dnsmasq --test --conf-file={config_file}\""
        test_result = subprocess.run(test_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if test_result.returncode != 0:
            print(f"[DNSMASQ] Configuration test failed: {test_result.stderr.decode('utf-8')}")
            return False
        
        # Execute dnsmasq with su privileges and explicit pid-file option
        # Use a direct command that will work reliably on Android
        cmd = f"su -c \"dnsmasq --conf-file={config_file} --pid-file={pid_file} --no-daemon\""
        
        # Start dnsmasq in a separate process
        with open(f'{user_dir}/start_dnsmasq.sh', 'w') as f:
            f.write(f"#!/system/bin/sh\n{cmd} > {log_file} 2>&1 &\n")
        os.chmod(f'{user_dir}/start_dnsmasq.sh', 0o755)
        
        # Execute the script
        subprocess.call(f"su -c \"sh {user_dir}/start_dnsmasq.sh\"", shell=True)
        
        # Give dnsmasq a moment to start up
        import time
        time.sleep(1)
        
        # Check if dnsmasq is running
        check_cmd = f"su -c \"ps | grep dnsmasq | grep {user_id}\""
        check_result = subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if check_result.returncode == 0:
            print(f"[DNSMASQ] Started dnsmasq for user {user_id}")
            return True
        else:
            # Check the log file for errors
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_content = f.read()
                print(f"[DNSMASQ] Failed to start dnsmasq. Log content: {log_content}")
            else:
                print(f"[DNSMASQ] Failed to start dnsmasq and no log file found")
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
