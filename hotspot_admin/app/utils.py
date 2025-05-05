import os
import subprocess
import re
from datetime import datetime
from flask import current_app
from .models import User, db

class NetworkManager:
    @staticmethod
    def get_interface_ip(interface):
        """Get IP address of an interface"""
        try:
            output = subprocess.check_output(['su', '-c', f'ip addr show {interface}']).decode()
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', output)
            return match.group(1) if match else None
        except:
            return None

    @staticmethod
    def find_hotspot_interface():
        """Find the active hotspot interface"""
        interfaces = ['ap0', 'wlan0', 'swlan0', 'wlan1']
        for iface in interfaces:
            try:
                output = subprocess.check_output(['su', '-c', f'ip link show {iface}']).decode()
                if '<UP,' in output:
                    ip = NetworkManager.get_interface_ip(iface)
                    if ip and ip.startswith('192.168.43.'):
                        return iface
            except:
                continue
        return 'ap0'  # Fallback to default

    @staticmethod
    def init_network():
        """Initialize network configuration"""
        # Find active hotspot interface
        active_interface = NetworkManager.find_hotspot_interface()
        current_app.config['HOTSPOT_INTERFACE'] = active_interface
        
        # Execute initialization commands
        commands = [
            # Enable IP forwarding
            'echo 1 > /proc/sys/net/ipv4/ip_forward',
            
            # Basic NAT setup
            f'iptables -t nat -A POSTROUTING -s {current_app.config["HOTSPOT_SUBNET"]} -o {current_app.config["WAN_INTERFACE"]} -j MASQUERADE',
            f'iptables -A FORWARD -i {active_interface} -o {current_app.config["WAN_INTERFACE"]} -j ACCEPT',
            f'iptables -A FORWARD -i {current_app.config["WAN_INTERFACE"]} -o {active_interface} -m state --state RELATED,ESTABLISHED -j ACCEPT'
        ]
        
        for cmd in commands:
            try:
                subprocess.run(['su', '-c', cmd], check=True)
            except Exception as e:
                print(f"Error executing command {cmd}: {e}")

    @staticmethod
    def get_connected_devices():
        """Get list of connected devices using multiple methods"""
        devices = []
        interface = current_app.config['HOTSPOT_INTERFACE']

        # Try ip neigh command
        try:
            arp_output = subprocess.check_output(['su', '-c', f'ip neigh show']).decode()
            for line in arp_output.splitlines():
                if interface in line:
                    match = re.match(r'([\d.]+) .* ([0-9a-fA-F:]{17})', line.upper())
                    if match:
                        ip, mac = match.groups()
                        if ip.startswith('192.168.43.'):
                            devices.append({
                                'ip_address': ip,
                                'mac_address': mac,
                                'hostname': NetworkManager.get_hostname(ip)
                            })
        except Exception as e:
            print(f"Error getting devices via ip neigh: {e}")

        # Try reading DHCP leases file
        if not devices:
            try:
                with open('/data/local/tmp/dnsmasq.leases', 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            devices.append({
                                'ip_address': parts[2],
                                'mac_address': parts[1].upper(),
                                'hostname': parts[3] if parts[3] != '*' else 'Unknown'
                            })
            except Exception as e:
                print(f"Error reading DHCP leases: {e}")

        # Try arp command as last resort
        if not devices:
            try:
                arp_output = subprocess.check_output(['su', '-c', 'arp -n']).decode()
                for line in arp_output.splitlines()[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 3:
                        ip, mac = parts[0], parts[2].upper()
                        if ip.startswith('192.168.43.'):
                            devices.append({
                                'ip_address': ip,
                                'mac_address': mac,
                                'hostname': NetworkManager.get_hostname(ip)
                            })
            except Exception as e:
                print(f"Error getting devices via arp: {e}")

        return devices

    @staticmethod
    def get_hostname(ip):
        """Try to get hostname for an IP address"""
        try:
            for cmd in [
                f'getprop net.{current_app.config["HOTSPOT_INTERFACE"]}.hostname',
                'getprop net.hostname',
                f'host {ip}',
                f'nslookup {ip}'
            ]:
                try:
                    output = subprocess.check_output(['su', '-c', cmd], timeout=1).decode().strip()
                    if output and 'not found' not in output.lower():
                        return output
                except:
                    continue
        except:
            pass
        return 'Unknown'

    @staticmethod
    def sync_connected_devices():
        """Sync connected devices with database"""
        connected_devices = NetworkManager.get_connected_devices()
        
        # Update database with connected devices
        for device in connected_devices:
            user = User.query.filter_by(mac_address=device['mac_address']).first()
            if not user:
                user = User(
                    mac_address=device['mac_address'],
                    hostname=device['hostname'],
                    ip_address=device['ip_address']
                )
                db.session.add(user)
            else:
                user.ip_address = device['ip_address']
                user.hostname = device['hostname']
                user.is_active = True
                user.last_seen = datetime.utcnow()
        
        # Mark disconnected devices as inactive
        connected_macs = [d['mac_address'] for d in connected_devices]
        User.query.filter(~User.mac_address.in_(connected_macs) if connected_macs else True).update(
            {'is_active': False}, synchronize_session=False
        )
        
        db.session.commit()

class DNSManager:
    @staticmethod
    def create_dnsmasq_config(blocked_domains, redirect_ip='127.0.0.1'):
        config_content = [
            f"port={current_app.config['DNS_PORT']}",
            "no-resolv",
            "no-poll",
            "no-hosts",
            f"interface={current_app.config['HOTSPOT_INTERFACE']}",
            f"listen-address={current_app.config['HOTSPOT_IP']}",
            # DHCP configuration
            f"dhcp-range={current_app.config['DHCP_RANGE_START']},{current_app.config['DHCP_RANGE_END']},12h",
            f"dhcp-option=option:router,{current_app.config['HOTSPOT_IP']}",
            f"dhcp-option=option:dns-server,{current_app.config['HOTSPOT_IP']}",
            "dhcp-authoritative",
            f"dhcp-leasefile=/data/local/tmp/dnsmasq.leases"
        ]
        
        # Add upstream DNS servers
        for dns in current_app.config['UPSTREAM_DNS']:
            config_content.append(f"server={dns}")
        
        # Add blocked domains
        for domain in blocked_domains:
            config_content.append(f"address=/{domain}/{redirect_ip}")
        
        config_content.append(f"log-facility={current_app.config['DNSMASQ_LOG_PATH']}")
        
        os.makedirs(os.path.dirname(current_app.config['DNSMASQ_CONF_PATH']), exist_ok=True)
        with open(current_app.config['DNSMASQ_CONF_PATH'], 'w') as f:
            f.write('\n'.join(config_content))

    @staticmethod
    def start_dnsmasq():
        try:
            DNSManager.stop_dnsmasq()
        except:
            pass

        # Kill any existing dnsmasq processes
        try:
            subprocess.run(['su', '-c', 'killall dnsmasq'], check=False)
        except:
            pass

        cmd = [
            "su",
            "-c",
            f"dnsmasq --conf-file={current_app.config['DNSMASQ_CONF_PATH']} " +
            f"--pid-file={current_app.config['DNSMASQ_PID_PATH']} " +
            "--no-daemon"
        ]
        return subprocess.Popen(cmd)

    @staticmethod
    def stop_dnsmasq():
        try:
            with open(current_app.config['DNSMASQ_PID_PATH'], 'r') as f:
                pid = int(f.read().strip())
                subprocess.run(['su', '-c', f'kill -15 {pid}'], check=True)
            os.remove(current_app.config['DNSMASQ_PID_PATH'])
            return True
        except (FileNotFoundError, ProcessLookupError):
            return False

class IPTablesManager:
    @staticmethod
    def execute_iptables_command(command):
        full_command = f"iptables {command}"
        subprocess.run(['su', '-c', full_command], check=True)

    @staticmethod
    def init_rules():
        """Initialize base iptables rules"""
        IPTablesManager.clear_rules()
        NetworkManager.init_network()
        IPTablesManager.add_dns_redirect_rules()
        IPTablesManager.add_http_redirect_rules()

    @staticmethod
    def add_dns_redirect_rules():
        iface = current_app.config['HOTSPOT_INTERFACE']
        dns_port = current_app.config['DNS_PORT']
        
        commands = [
            f"-t nat -I PREROUTING -i {iface} -p udp --dport 53 -j REDIRECT --to-port {dns_port}",
            f"-t nat -I PREROUTING -i {iface} -p tcp --dport 53 -j REDIRECT --to-port {dns_port}"
        ]
        
        for cmd in commands:
            IPTablesManager.execute_iptables_command(cmd)

    @staticmethod
    def add_http_redirect_rules():
        iface = current_app.config['HOTSPOT_INTERFACE']
        http_port = current_app.config['HTTP_PORT']
        https_port = current_app.config['HTTPS_PORT']
        
        commands = [
            f"-t nat -I PREROUTING -i {iface} -p tcp --dport 80 -j REDIRECT --to-port {http_port}",
            f"-t nat -I PREROUTING -i {iface} -p tcp --dport 443 -j REDIRECT --to-port {https_port}"
        ]
        
        for cmd in commands:
            IPTablesManager.execute_iptables_command(cmd)

    @staticmethod
    def clear_rules():
        subprocess.run(['su', '-c', 'iptables -t nat -F PREROUTING'], check=True)
