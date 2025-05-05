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
    DNSMASQ_PID_PATH = '/sdcard/dnsmasq.pid'
    DNS_PORT = 1053
    HTTP_PORT = 8000
    HTTPS_PORT = 8000
    
    # Network interface configuration
    HOTSPOT_INTERFACE = 'ap0'
    WAN_INTERFACE = 'wlan0'  # Interface connected to internet
    
    # DHCP Range for hotspot clients
    DHCP_RANGE_START = '192.168.43.2'
    DHCP_RANGE_END = '192.168.43.254'
    HOTSPOT_SUBNET = '192.168.43.0/24'
    HOTSPOT_IP = '192.168.43.1'  # Hotspot's own IP

    # DNS Servers for upstream resolution
    UPSTREAM_DNS = ['8.8.8.8', '8.8.4.4']

    # Device scanning interval (seconds)
    DEVICE_SCAN_INTERVAL = 30

    # Network initialization commands
    INIT_COMMANDS = [
        f'ip addr add {HOTSPOT_IP}/24 dev {HOTSPOT_INTERFACE}',
        f'ip link set {HOTSPOT_INTERFACE} up',
        'echo 1 > /proc/sys/net/ipv4/ip_forward',
        f'iptables -t nat -A POSTROUTING -s {HOTSPOT_SUBNET} -o {WAN_INTERFACE} -j MASQUERADE',
    ]
