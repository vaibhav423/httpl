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
    
    # Get app names using application-label
    apps = []
    # Run the command in shell to get app names
    name_cmd = "pm list packages -3 | while read -r line; do pkg=$(echo $line | cut -d':' -f2); app=$(dumpsys package \"$pkg\" | grep -m 1 \"application-label:\" | cut -d':' -f2); echo \"$app : $pkg\"; done"
    output = run_adb_command(['shell', name_cmd])
    
    if output:
        for line in output.splitlines():
            if ':' in line:
                parts = line.split(' : ')
                if len(parts) == 2:
                    name = parts[0].strip().strip("'")  # Remove quotes and whitespace
                    package = parts[1].strip()
                    
                    if not name:  # Fallback to package name if label is empty
                        name = package.split('.')[-1].capitalize()
                        
                    apps.append({'package': package, 'name': name})
    
    return jsonify({'status': 'success', 'apps': apps})

@app.route('/save-config', methods=['POST'])
def save_device_config():
    name = request.form.get('name')
    ip_address = request.form.get('ip_address')
    apps = request.form.get('apps')
    
    if not name or not ip_address or not apps:
        return jsonify({'status': 'error', 'message': 'Missing required data'})
    
    try:
        apps = eval(apps)  # Convert string representation of list to actual list
        save_config(name, ip_address, apps)
        return jsonify({'status': 'success', 'message': f'Configuration "{name}" saved successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to save configuration: {str(e)}'})

@app.route('/load-config', methods=['GET'])
def load_device_config():
    name = request.args.get('name')
    config = load_config(name)
    if config:
        if name:
            return jsonify({'status': 'success', 'config': config})
        return jsonify({'status': 'success', 'configs': config})
    return jsonify({'status': 'error', 'message': 'No configuration found'})

@app.route('/delete-config', methods=['POST'])
def delete_device_config():
    name = request.form.get('name')
    if not name:
        return jsonify({'status': 'error', 'message': 'Configuration name is required'})
    
    if delete_config(name):
        return jsonify({'status': 'success', 'message': f'Configuration "{name}" deleted successfully'})
    return jsonify({'status': 'error', 'message': f'Failed to delete configuration "{name}"'})

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

@app.route('/foreground-app')
def get_foreground_app():
    # Get the current foreground app using dumpsys
    cmd = "dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp' | cut -d'/' -f1 | grep -o '[^ ]*$'"
    result = run_adb_command(['shell', cmd])
    
    if result:
        # Get the app name for this package
        package_name = result.strip()
        name_cmd = f"dumpsys package \"{package_name}\" | grep -m 1 \"application-label:\" | cut -d':' -f2"
        name_result = run_adb_command(['shell', name_cmd])
        
        app_name = name_result.strip().strip("'") if name_result else package_name
        return jsonify({
            'status': 'success',
            'package': package_name,
            'name': app_name
        })
    
    return jsonify({
        'status': 'error',
        'message': 'Failed to get foreground app'
    })
