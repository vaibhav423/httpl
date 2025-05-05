import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hotspot.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # DNS and Network configuration
    DNSMASQ_CONF_PATH = '/data/local/tmp/dns_spoof/dnsmasq.conf'
    DNSMASQ_LOG_PATH = '/data/local/tmp/dnsmasq.log'
    DNSMASQ_PID_PATH = '/data/local/tmp/dnsmasq.pid'
    DNSMASQ_LEASE_PATH = '/data/local/tmp/dnsmasq.leases'
    DNS_PORT = 53  # Use standard DNS port
    HTTP_PORT = 8000
    HTTPS_PORT = 8000
    
    # Network interface configuration
    HOTSPOT_INTERFACE = 'ap0'  # Will be auto-detected
    WAN_INTERFACE = 'wlan0'  # Interface connected to internet
    
    # DHCP Range for hotspot clients (Android default)
    DHCP_RANGE_START = '192.168.43.2'
    DHCP_RANGE_END = '192.168.43.254'
    HOTSPOT_SUBNET = '192.168.43.0/24'
    HOTSPOT_IP = '192.168.43.1'  # Android's default hotspot IP

    # DNS Servers (Cloudflare and Google)
    UPSTREAM_DNS = ['1.1.1.1', '8.8.8.8']

    # Device scanning interval (seconds)
    DEVICE_SCAN_INTERVAL = 30

    # Android-specific paths
    ANDROID_PROP_PATH = '/system/build.prop'
    ANDROID_DHCP_PATH = '/data/misc/dhcp'

    # Base iptables initialization commands
    INIT_COMMANDS = [
        # Clear any existing rules
        'iptables -F',
        'iptables -t nat -F',
        'iptables -t mangle -F',
        
        # Enable IP forwarding
        'echo 1 > /proc/sys/net/ipv4/ip_forward',
        
        # Allow established connections
        'iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT',
        'iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT',
        
        # Allow traffic on hotspot interface
        'iptables -A INPUT -i {iface} -j ACCEPT',
        'iptables -A FORWARD -i {iface} -j ACCEPT',
        
        # NAT configuration
        'iptables -t nat -A POSTROUTING -s {subnet} -o {wan_iface} -j MASQUERADE',
        
        # Allow DNS traffic
        'iptables -A INPUT -p udp --dport 53 -j ACCEPT',
        'iptables -A INPUT -p tcp --dport 53 -j ACCEPT',
        
        # Allow DHCP
        'iptables -A INPUT -p udp --dport 67:68 -j ACCEPT',
    ]
