from flask import render_template, request, jsonify
from app import app
from app.config import save_config, load_config
import subprocess
import re

def run_adb_command(command):
    try:
        result = subprocess.run(['adb'] + command, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect_device():
    ip_address = request.form.get('ip_address')
    if not ip_address:
        return jsonify({'status': 'error', 'message': 'IP address is required'})
    
    # Kill existing ADB server and start fresh
    run_adb_command(['kill-server'])
    run_adb_command(['start-server'])
    
    # Try to connect to the device
    result = run_adb_command(['connect', ip_address])
    
    if 'connected' in result.lower():
        return jsonify({'status': 'success', 'message': result})
    else:
        return jsonify({'status': 'error', 'message': result})

@app.route('/list-apps')
def list_apps():
    # Get list of installed packages
    output = run_adb_command(['shell', 'pm', 'list', 'packages', '-3'])
    
    if not output:
        return jsonify({'status': 'error', 'message': 'Failed to get app list'})
    
    # Parse package names
    packages = [line.split(':')[1] for line in output.splitlines() if ':' in line]
    
    # Get app names for each package
    apps = []
    for package in packages:
        # Get the app's label (name)
        name_output = run_adb_command(['shell', 'dumpsys', 'package', package, '|', 'grep', 'android.intent.action.MAIN'])
        if not name_output:
            continue

        label_cmd = ['shell', 'cmd', 'package', 'resolve-activity', '--brief', package]
        label_output = run_adb_command(label_cmd)
        
        if label_output and 'label=' in label_output:
            name = label_output.split('label=')[-1].split(' ')[0].strip()
        else:
            # Fallback to package name if can't get app name
            name = package.split('.')[-1].capitalize()
            
        apps.append({'package': package, 'name': name})
    
    return jsonify({'status': 'success', 'apps': apps})

@app.route('/save-config', methods=['POST'])
def save_device_config():
    ip_address = request.form.get('ip_address')
    apps = request.form.get('apps')
    
    if not ip_address or not apps:
        return jsonify({'status': 'error', 'message': 'Missing required data'})
    
    try:
        apps = eval(apps)  # Convert string representation of list to actual list
        save_config(ip_address, apps)
        return jsonify({'status': 'success', 'message': 'Configuration saved successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save configuration: {str(e)}'})

@app.route('/load-config')
def load_device_config():
    config = load_config()
    if config:
        return jsonify({'status': 'success', 'config': config})
    return jsonify({'status': 'error', 'message': 'No saved configuration found'})

@app.route('/launch-app', methods=['POST'])
def launch_app():
    package_name = request.form.get('package')
    if not package_name:
        return jsonify({'status': 'error', 'message': 'Package name is required'})
    
    # Launch the app using monkey
    result = run_adb_command(['shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'])
    
    if 'Events injected' in result:
        return jsonify({'status': 'success', 'message': f'Launched {package_name}'})
    else:
        return jsonify({'status': 'error', 'message': f'Failed to launch {package_name}'})
