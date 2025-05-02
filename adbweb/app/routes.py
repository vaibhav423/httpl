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
    # Get list of installed packages with their names
    name_cmd = (
        "for pkg in $(pm list packages -3 | cut -d':' -f2); do "
        "label=$(dumpsys package $pkg | grep -E 'application-label:|applicationInfo.*label=' | head -n1); "
        "if [ -n \"$label\" ]; then "
        "echo \"$label : $pkg\"; "
        "else "
        "echo \"$pkg : $pkg\"; "
        "fi; "
        "done"
    )
    output = run_adb_command(['shell', name_cmd])
    
    if not output:
        return jsonify({'status': 'error', 'message': 'Failed to get app list'})
    
    apps = []
    
    if output:
        for line in output.splitlines():
            if ':' in line:
                parts = line.split(' : ')
                if len(parts) == 2:
                    package = parts[1].strip()
                    # Extract name from label output
                    label_match = re.search(r'(?:application-label:|applicationInfo.*?label=)\'([^\']+)\'', parts[0])
                    if label_match:
                        name = label_match.group(1)
                    else:
                        # Fallback to making package name more readable
                        name = package.split('.')[-1].replace('_', ' ').title()
                        
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

@app.route('/force-stop', methods=['POST'])
def force_stop_app():
    package_name = request.form.get('package')
    if not package_name:
        return jsonify({'status': 'error', 'message': 'Package name is required'})
    
    result = run_adb_command(['shell', 'am', 'force-stop', package_name])
    return jsonify({
        'status': 'success',
        'message': f'Force stopped {package_name}'
    })

@app.route('/uninstall', methods=['POST'])
def uninstall_app():
    package_name = request.form.get('package')
    if not package_name:
        return jsonify({'status': 'error', 'message': 'Package name is required'})
    
    result = run_adb_command(['shell', 'pm', 'uninstall', package_name])
    if 'Success' in result:
        return jsonify({
            'status': 'success',
            'message': f'Uninstalled {package_name}'
        })
    return jsonify({
        'status': 'error',
        'message': f'Failed to uninstall: {result}'
    })

@app.route('/delete-config', methods=['POST'])
def delete_device_config():
    name = request.form.get('name')
    if not name:
        return jsonify({'status': 'error', 'message': 'Configuration name is required'})
    
    try:
        if delete_config(name):
            return jsonify({'status': 'success', 'message': f'Configuration "{name}" deleted successfully'})
        return jsonify({'status': 'error', 'message': f'Failed to delete configuration "{name}"'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

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

@app.route('/lookup-mac', methods=['POST'])
def lookup_mac():
    mac = request.form.get('mac')
    if not mac:
        return jsonify({'status': 'error', 'message': 'MAC address is required'})
    
    try:
        # Run the arp lookup command
        command = f"sudo awk -v mac=\"{mac}\" 'tolower($4)==tolower(mac) {{print $1}}' /proc/net/arp"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        ip = result.stdout.strip()
        if ip:
            return jsonify({'status': 'success', 'ip': ip})
        else:
            return jsonify({'status': 'error', 'message': 'No IP found for this MAC address'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error looking up MAC address: {str(e)}'})

@app.route('/foreground-app')
def get_foreground_app():
    # Try to get the current foreground activity
    result = run_adb_command(['shell', 'dumpsys activity activities'])
    
    if not result:
        return jsonify({
            'status': 'error',
            'message': 'Failed to get activity state'
        })

    # Try both activity manager and window service
    package_name = None
    
    # Activity manager check
    activity_patterns = [
        r'mResumedActivity.*?([a-zA-Z0-9_.]+)/[^}]*',
        r'mFocusedActivity.*?([a-zA-Z0-9_.]+)/[^}]*'
    ]
    for pattern in activity_patterns:
        match = re.search(pattern, result)
        if match:
            package_name = match.group(1)
            break
            
    # Window service check if activity manager failed
    if not package_name:
        window_result = run_adb_command(['shell', 'dumpsys window displays'])
        if window_result:
            window_patterns = [
                r'mCurrentFocus.*?([a-zA-Z0-9_.]+)/[^}]*',
                r'focusedApp.*?([a-zA-Z0-9_.]+)/[^}]*'
            ]
            for pattern in window_patterns:
                match = re.search(pattern, window_result)
                if match:
                    package_name = match.group(1)
                    break

    if package_name:
        # Just return the package name itself
        app_name = package_name

        return jsonify({
            'status': 'success',
            'package': package_name,
            'name': app_name
        })
    
    return jsonify({
        'status': 'error',
        'message': 'No foreground app found'
    })
