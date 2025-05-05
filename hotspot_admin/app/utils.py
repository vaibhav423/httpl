import os
import subprocess
from flask import current_app

class DNSManager:
    @staticmethod
    def create_dnsmasq_config(blocked_domains, redirect_ip='127.0.0.1'):
        config_content = [
            f"port={current_app.config['DNS_PORT']}",
            "no-resolv"
        ]
        
        for domain in blocked_domains:
            config_content.append(f"address=/{domain}/{redirect_ip}")
        
        config_content.append(f"log-facility={current_app.config['DNSMASQ_LOG_PATH']}")
        
        os.makedirs(os.path.dirname(current_app.config['DNSMASQ_CONF_PATH']), exist_ok=True)
        with open(current_app.config['DNSMASQ_CONF_PATH'], 'w') as f:
            f.write('\n'.join(config_content))

    @staticmethod
    def start_dnsmasq():
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
                subprocess.run(['su', '-c', f'kill -15 {pid}'])
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
