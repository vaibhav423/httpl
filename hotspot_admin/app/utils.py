import os
import subprocess
from flask import current_app
import iptc

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
            "dnsmasq",
            f"--conf-file={current_app.config['DNSMASQ_CONF_PATH']}",
            f"--pid-file={current_app.config['DNSMASQ_PID_PATH']}",
            "--no-daemon"
        ]
        return subprocess.Popen(cmd)

    @staticmethod
    def stop_dnsmasq():
        try:
            with open(current_app.config['DNSMASQ_PID_PATH'], 'r') as f:
                pid = int(f.read().strip())
                os.kill(pid, 15)  # SIGTERM
            os.remove(current_app.config['DNSMASQ_PID_PATH'])
            return True
        except (FileNotFoundError, ProcessLookupError):
            return False

class IPTablesManager:
    @staticmethod
    def add_dns_redirect_rules():
        iface = current_app.config['HOTSPOT_INTERFACE']
        dns_port = current_app.config['DNS_PORT']
        
        # UDP DNS redirect
        rule_udp = {
            'protocol': 'udp',
            'dst': '53',
            'to-port': str(dns_port),
            'target': 'REDIRECT'
        }
        
        # TCP DNS redirect
        rule_tcp = {
            'protocol': 'tcp',
            'dst': '53',
            'to-port': str(dns_port),
            'target': 'REDIRECT'
        }
        
        chain = iptc.Chain(iptc.Table(iptc.Table.NAT), "PREROUTING")
        
        for rule in [rule_udp, rule_tcp]:
            rule['in-interface'] = iface
            iptc_rule = iptc.Rule()
            for key, value in rule.items():
                setattr(iptc_rule, key.replace('-', '_'), value)
            chain.insert_rule(iptc_rule)

    @staticmethod
    def add_http_redirect_rules():
        iface = current_app.config['HOTSPOT_INTERFACE']
        http_port = current_app.config['HTTP_PORT']
        https_port = current_app.config['HTTPS_PORT']
        
        rules = [
            # HTTP redirect
            {
                'protocol': 'tcp',
                'dst': '80',
                'to-port': str(http_port),
                'target': 'REDIRECT'
            },
            # HTTPS redirect
            {
                'protocol': 'tcp',
                'dst': '443',
                'to-port': str(https_port),
                'target': 'REDIRECT'
            }
        ]
        
        chain = iptc.Chain(iptc.Table(iptc.Table.NAT), "PREROUTING")
        
        for rule in rules:
            rule['in-interface'] = iface
            iptc_rule = iptc.Rule()
            for key, value in rule.items():
                setattr(iptc_rule, key.replace('-', '_'), value)
            chain.insert_rule(iptc_rule)

    @staticmethod
    def clear_rules():
        table = iptc.Table(iptc.Table.NAT)
        chain = iptc.Chain(table, "PREROUTING")
        chain.flush()
