import json
import os

CONFIG_FILE = 'device_configs.json'

def save_config(name, ip_address, apps):
    configs = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                configs = json.load(f)
        except:
            pass
    
    configs[name] = {
        'ip_address': ip_address,
        'apps': apps
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(configs, f, indent=2)

def load_config(name=None):
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r') as f:
            configs = json.load(f)
            if name:
                return configs.get(name)
            return configs
    except:
        return None

def delete_config(name):
    if not os.path.exists(CONFIG_FILE):
        return False
    try:
        with open(CONFIG_FILE, 'r') as f:
            configs = json.load(f)
        
        if name in configs:
            del configs[name]
            with open(CONFIG_FILE, 'w') as f:
                json.dump(configs, f, indent=2)
            return True
    except:
        pass
    return False
