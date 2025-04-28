from flask import render_template, request, jsonify
from app import app
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
        name_output = run_adb_command(['shell', 'dumpsys', 'package', package, '|', 'grep', 'versionName'])
        name = package  # Default to package name if we can't get the app name
        if name_output:
            name = f"{package} ({name_output.strip()})"
        apps.append({'package': package, 'name': name})
    
    return jsonify({'status': 'success', 'apps': apps})

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
