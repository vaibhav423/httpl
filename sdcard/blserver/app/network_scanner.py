import subprocess
import re
import socket
import os
import glob

def get_interface_ip(ifname):
    """Get IP address of a network interface"""
    try:
        # For Android/Linux
        cmd = f"ip addr show {ifname} | grep 'inet ' | awk '{{print $2}}' | cut -d/ -f1"
        result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        return result
    except Exception as e:
        print(f"Error getting IP for interface {ifname}: {e}")
        return None

def get_network_interfaces():
    """Get list of network interfaces"""
    interfaces = []
    try:
        # For Android/Linux
        output = subprocess.check_output("ip link show | grep -v lo | grep 'state UP'", shell=True).decode('utf-8')
        pattern = r'\d+: ([^:@]+)[@:]'
        for line in output.split('\n'):
            match = re.search(pattern, line)
            if match and match.group(1) != 'lo':
                interfaces.append(match.group(1))
    except Exception as e:
        print(f"Error getting interfaces: {e}")
        # Fallback to common interfaces
        interfaces = ['wlan0', 'eth0', 'ap0']
    return interfaces

def scan_network(interface):
    """Scan network for connected devices"""
    devices = []
    try:
        # Get interface IP and subnet
        ip = get_interface_ip(interface)
        if not ip:
            return devices
            
        subnet = '.'.join(ip.split('.')[0:3]) + '.'
        
        # Run ARP scan (works on Android with root)
        cmd = f"ip neigh show dev {interface}"
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        # Parse output
        for line in output.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 1:
                    ip_addr = parts[0]
                    mac_addr = parts[4] if len(parts) > 4 else "Unknown"
                    hostname = get_hostname(ip_addr)
                    devices.append({
                        'ip': ip_addr,
                        'mac': mac_addr,
                        'hostname': hostname,
                        'has_dns': check_if_dns_exists(ip_addr)
                    })
    except Exception as e:
        print(f"Error scanning network: {e}")
        # Fallback to ping scan
        try:
            ip = get_interface_ip(interface)
            if not ip:
                return devices
                
            subnet = '.'.join(ip.split('.')[0:3]) + '.'
            
            # Ping scan (slower but more compatible)
            for i in range(1, 255):
                target_ip = f"{subnet}{i}"
                response = subprocess.call(
                    ['ping', '-c', '1', '-W', '1', target_ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                if response == 0:
                    hostname = get_hostname(target_ip)
                    devices.append({
                        'ip': target_ip,
                        'mac': "Unknown",
                        'hostname': hostname,
                        'has_dns': check_if_dns_exists(target_ip)
                    })
        except Exception as e:
            print(f"Error with fallback scan: {e}")
    
    return devices

def get_hostname(ip):
    """Try to get hostname from IP"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except:
        return "Unknown"

def check_if_dns_exists(ip):
    """Check if DNS configuration exists for this IP"""
    # Check if any user has this IP
    for user_dir in glob.glob('/sdcard/blserver/conf/users/*/'):
        user_id = os.path.basename(os.path.dirname(user_dir))
        user_ip_file = f"/sdcard/blserver/conf/users/{user_id}/ip.txt"
        if os.path.exists(user_ip_file):
            with open(user_ip_file, 'r') as f:
                if f.read().strip() == ip:
                    return True
    return False
