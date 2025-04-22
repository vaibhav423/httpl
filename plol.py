from flask import Flask, jsonify, request, render_template_string
import subprocess
import re
from datetime import datetime
import json
import os
import atexit
import signal
import sys

# Initialize with current timestamp and user info
CURRENT_DATETIME = "2025-04-22 14:13:24"  # Current UTC time in YYYY-MM-DD HH:MM:SS format
CURRENT_USER = "vaibhav423"

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Device Manager</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #2563eb;
            --success-color: #22c55e;
            --danger-color: #ef4444;
            --background-light: #f8fafc;
            --text-light: #1e293b;
            --card-light: #ffffff;
            --background-dark: #0f172a;
            --text-dark: #e2e8f0;
            --card-dark: #1e293b;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            transition: background-color 0.3s, color 0.3s;
        }

        body {
            font-family: 'Inter', sans-serif;
            line-height: 1.5;
            background-color: var(--background-light);
            color: var(--text-light);
        }

        body.dark-mode {
            background-color: var(--background-dark);
            color: var(--text-dark);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        .dark-mode .header {
            background: rgba(30, 41, 59, 0.8);
        }

        .header-title {
            margin-bottom: 10px;
        }

        .header-info {
            font-size: 0.9rem;
            color: #64748b;
            line-height: 1.4;
        }

        .dark-mode .header-info {
            color: #94a3b8;
        }

        .theme-toggle {
            background: none;
            border: 2px solid #cbd5e1;
            padding: 8px 16px;
            cursor: pointer;
            border-radius: 8px;
            color: inherit;
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }

        .theme-toggle:hover {
            background: rgba(203, 213, 225, 0.1);
            transform: scale(1.05);
        }

        .device-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .device-card {
            background: var(--card-light);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .dark-mode .device-card {
            background: var(--card-dark);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }

        .device-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.15);
        }

        .device-card.allowed {
            border-left: 4px solid var(--success-color);
        }

        .device-card.blocked {
            border-left: 4px solid var(--danger-color);
        }

        .device-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(203, 213, 225, 0.2);
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            position: relative;
        }

        .allowed .status-indicator {
            background-color: var(--success-color);
            box-shadow: 0 0 8px var(--success-color);
        }

        .blocked .status-indicator {
            background-color: var(--danger-color);
            box-shadow: 0 0 8px var(--danger-color);
        }

        .status-indicator::after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% {
                transform: scale(1);
                opacity: 0.8;
            }
            70% {
                transform: scale(2);
                opacity: 0;
            }
            100% {
                transform: scale(1);
                opacity: 0;
            }
        }

        .device-name {
            font-weight: 600;
            font-size: 1.1rem;
            flex-grow: 1;
        }

        .device-info {
            margin: 15px 0;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 8px 0;
            border-bottom: 1px dashed rgba(203, 213, 225, 0.2);
        }

        .info-label {
            color: #64748b;
            font-size: 0.85rem;
            font-weight: 500;
        }

        .dark-mode .info-label {
            color: #94a3b8;
        }

        .info-value {
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.9rem;
        }

        .toggle-button {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .allowed .toggle-button {
            background-color: var(--danger-color);
            color: white;
        }

        .blocked .toggle-button {
            background-color: var(--success-color);
            color: white;
        }

        .toggle-button:hover {
            transform: translateY(-1px);
            filter: brightness(1.1);
        }

        .toggle-button:active {
            transform: translateY(1px);
        }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 15px 25px;
            background: var(--card-light);
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }

        .dark-mode .toast {
            background: var(--card-dark);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        .loading {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(to right, var(--primary-color), var(--success-color));
            z-index: 1000;
        }

        .loading::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to right, transparent, white, transparent);
            animation: loading 1.5s infinite;
        }

        @keyframes loading {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        @media (max-width: 768px) {
            .container { padding: 10px; }
            .device-grid { grid-template-columns: 1fr; }
            .header {
                flex-direction: column;
                gap: 15px;
                text-align: center;
            }
            .theme-toggle {
                width: 100%;
                margin-top: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="loading" id="loadingBar" style="display: none;"></div>
    <div class="container">
        <div class="header">
            <div>
                <h1 class="header-title">Network Device Manager</h1>
                <div class="header-info">
                    <div>Current Date and Time (UTC): ''' + CURRENT_DATETIME + '''</div>
                    <div>Current User's Login: ''' + CURRENT_USER + '''</div>
                </div>
            </div>
            <button class="theme-toggle" onclick="toggleTheme()">🌓 Toggle Theme</button>
        </div>
        <div class="device-grid" id="deviceList"></div>
    </div>

    <script>
        let isDarkMode = localStorage.getItem('darkMode') === 'true';
        
        function toggleTheme() {
            document.body.classList.toggle('dark-mode');
            isDarkMode = !isDarkMode;
            localStorage.setItem('darkMode', isDarkMode);
        }

        // Initialize theme
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
        }

        function showToast(message, isError = false) {
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.innerHTML = `
                <span style="color: ${isError ? 'var(--danger-color)' : 'var(--success-color)'}">
                    ${isError ? '❌' : '✅'}
                </span>
                <span>${message}</span>
            `;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }

        function toggleLoading(show) {
            document.getElementById('loadingBar').style.display = show ? 'block' : 'none';
        }

        function formatTimestamp(timestamp) {
            return new Date(timestamp).toLocaleString();
        }

        function updateDeviceList() {
            toggleLoading(true);
            fetch('/api/devices')
                .then(response => response.json())
                .then(devices => {
                    const deviceList = document.getElementById('deviceList');
                    deviceList.innerHTML = '';
                    
                    devices.forEach(device => {
                        const deviceCard = document.createElement('div');
                        deviceCard.className = `device-card ${device.allowed ? 'allowed' : 'blocked'}`;
                        
                        const buttonText = device.allowed ? 'Block Access' : 'Allow Access';
                        const statusText = device.allowed ? 'Allowed' : 'Blocked';
                        
                        deviceCard.innerHTML = `
                            <div class="device-header">
                                <span class="status-indicator"></span>
                                <span class="device-name">${device.name || 'Unknown Device'}</span>
                            </div>
                            <div class="device-info">
                                <div class="info-row">
                                    <span class="info-label">Status</span>
                                    <span class="info-value ${device.allowed ? 'text-success' : 'text-danger'}">
                                        ${statusText}
                                    </span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">MAC Address</span>
                                    <span class="info-value">${device.mac}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">IP Address</span>
                                    <span class="info-value">${device.ip}</span>
                                </div>
                            </div>
                            <button 
                                class="toggle-button" 
                                onclick="toggleAccess('${device.mac}')"
                            >
                                ${buttonText}
                            </button>
                        `;
                        deviceList.appendChild(deviceCard);
                    });
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Failed to fetch devices', true);
                })
                .finally(() => {
                    toggleLoading(false);
                });
        }

        function toggleAccess(mac) {
            toggleLoading(true);
            fetch('/api/toggle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mac: mac })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateDeviceList();
                    showToast('Device access updated successfully');
                } else {
                    showToast('Failed to update device access', true);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('An error occurred', true);
            })
            .finally(() => {
                toggleLoading(false);
            });
        }

        // Initial update and set interval
        updateDeviceList();
        setInterval(updateDeviceList, 5000);
    </script>
</body>
</html>
'''
class HotspotManager:
    def __init__(self):
        self.devices_file = "devices.json"
        self.load_devices()

    def load_devices(self):
        try:
            with open(self.devices_file, 'r') as f:
                self.devices = json.load(f)
        except FileNotFoundError:
            self.devices = {}

    def save_devices(self):
        with open(self.devices_file, 'w') as f:
            json.dump(self.devices, f)

    def get_connected_devices(self):
        try:
            # Get both IPv4 and IPv6 neighbors
            output_v4 = subprocess.check_output(['su', '-c', 'ip neigh show'], 
                                             universal_newlines=True)
            output_v6 = subprocess.check_output(['su', '-c', 'ip -6 neigh show'], 
                                             universal_newlines=True)
            
            devices = {}
            
            # Process IPv4 devices
            for line in output_v4.split('\n'):
                if line.strip():
                    match = re.match(r'(\d+\.\d+\.\d+\.\d+)\s+dev\s+\w+\s+lladdr\s+([0-9a-fA-F:]+)', line)
                    if match:
                        ip, mac = match.groups()
                        mac = mac.upper()
                        if mac not in devices:
                            devices[mac] = {
                                'ip': ip,
                                'ipv6': [],
                                'mac': mac,
                                'name': self.devices.get(mac, {}).get('name', 'Unknown Device'),
                                'allowed': self.devices.get(mac, {}).get('allowed', True)
                            }

            # Process IPv6 devices
            for line in output_v6.split('\n'):
                if line.strip():
                    match = re.match(r'([0-9a-fA-F:]+)\s+dev\s+\w+\s+lladdr\s+([0-9a-fA-F:]+)', line)
                    if match:
                        ipv6, mac = match.groups()
                        mac = mac.upper()
                        if mac in devices:
                            devices[mac]['ipv6'].append(ipv6)
                        else:
                            devices[mac] = {
                                'ip': 'N/A',
                                'ipv6': [ipv6],
                                'mac': mac,
                                'name': self.devices.get(mac, {}).get('name', 'Unknown Device'),
                                'allowed': self.devices.get(mac, {}).get('allowed', True)
                            }

            return list(devices.values())
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            return []

    def toggle_access(self, mac):
        mac = mac.upper()
        if mac not in self.devices:
            self.devices[mac] = {'allowed': True, 'name': 'Unknown Device'}
        
        self.devices[mac]['allowed'] = not self.devices[mac]['allowed']
        
        try:
            if not self.devices[mac]['allowed']:
                # Block IPv4
                subprocess.run(['su', '-c', f'iptables -I FORWARD -m mac --mac-source {mac} -j DROP'])
                subprocess.run(['su', '-c', f'iptables -I OUTPUT -m mac --mac-source {mac} -j DROP'])
                # Block IPv6
                subprocess.run(['su', '-c', f'ip6tables -I FORWARD -m mac --mac-source {mac} -j DROP'])
                subprocess.run(['su', '-c', f'ip6tables -I OUTPUT -m mac --mac-source {mac} -j DROP'])
            else:
                # Unblock IPv4
                subprocess.run(['su', '-c', f'iptables -D FORWARD -m mac --mac-source {mac} -j DROP'])
                subprocess.run(['su', '-c', f'iptables -D OUTPUT -m mac --mac-source {mac} -j DROP'])
                # Unblock IPv6
                subprocess.run(['su', '-c', f'ip6tables -D FORWARD -m mac --mac-source {mac} -j DROP'])
                subprocess.run(['su', '-c', f'ip6tables -D OUTPUT -m mac --mac-source {mac} -j DROP'])
        except subprocess.CalledProcessError as e:
            print(f"Error executing iptables/ip6tables command: {e}")
            return False

        self.save_devices()
        return True

hotspot_manager = HotspotManager()

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/devices')
def get_devices():
    devices = hotspot_manager.get_connected_devices()
    return jsonify(devices)

@app.route('/api/toggle', methods=['POST'])
def toggle_device():
    data = request.get_json()
    mac = data.get('mac')
    if mac:
        success = hotspot_manager.toggle_access(mac)
        return jsonify({'success': success})
    return jsonify({'success': False, 'error': 'No MAC address provided'})

if __name__ == '__main__':
    # Run the Flask app on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)

