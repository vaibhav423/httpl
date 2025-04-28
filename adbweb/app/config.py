import json
import os

CONFIG_FILE = 'device_config.json'

def save_config(ip_address, apps):
    config = {
        'ip_address': ip_address,
        'apps': apps
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return None
