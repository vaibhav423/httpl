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
