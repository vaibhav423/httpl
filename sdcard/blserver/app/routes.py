from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from . import dns_manager, network_scanner
import os
import json
import glob

bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    """Main dashboard"""
    # Get global settings
    global_settings = dns_manager.get_global_settings()
    
    # Get network interfaces
    interfaces = network_scanner.get_network_interfaces()
    
    # Get active users
    users = []
    for user_dir in glob.glob('/workspaces/httpl/sdcard/blserver/conf/users/*/'):
        user_id = os.path.basename(os.path.dirname(user_dir))
        user_ip_file = f"{user_dir}/ip.txt"
        if os.path.exists(user_ip_file):
            with open(user_ip_file, 'r') as f:
                ip = f.read().strip()
            users.append({
                'id': user_id,
                'ip': ip,
                'settings': dns_manager.get_user_settings(user_id)
            })
    
    return render_template('index.html', 
                          global_settings=global_settings,
                          interfaces=interfaces,
                          users=users)

@bp.route('/scan/<interface>')
def scan(interface):
    """Scan network for devices"""
    devices = network_scanner.scan_network(interface)
    return jsonify(devices)

@bp.route('/global-settings', methods=['POST'])
def update_global_settings():
    """Update global DNS settings"""
    settings = {
        'default_dns': request.form.get('default_dns', '1.1.1.1'),
        'global_override_enabled': request.form.get('global_override_enabled') == 'on',
        'global_override_ip': request.form.get('global_override_ip', '')
    }
    dns_manager.update_global_settings(settings)
    return redirect(url_for('routes.index'))

@bp.route('/create-dns', methods=['POST'])
def create_dns():
    """Create DNS for a device"""
    ip = request.form.get('ip')
    user_id = ip.replace('.', '_')  # Use IP as user ID (with dots replaced)
    dns_manager.create_user_dns(user_id, ip)
    return redirect(url_for('routes.index'))

@bp.route('/user/<user_id>', methods=['GET', 'POST'])
def user_settings(user_id):
    """User-specific settings"""
    if request.method == 'POST':
        settings = dns_manager.get_user_settings(user_id)
        settings['override_enabled'] = request.form.get('override_enabled') == 'on'
        settings['override_ip'] = request.form.get('override_ip', '')
        
        # Handle custom domains
        domains = {}
        for key, value in request.form.items():
            if key.startswith('domain_'):
                index = key.split('_')[1]
                domain = request.form.get(f'domain_{index}')
                ip = request.form.get(f'domain_ip_{index}')
                if domain and ip:
                    domains[domain] = ip
        
        settings['custom_domains'] = domains
        
        # Save settings
        user_dir = f'/workspaces/httpl/sdcard/blserver/conf/users/{user_id}'
        os.makedirs(user_dir, exist_ok=True)
        with open(f'{user_dir}/settings.json', 'w') as f:
            json.dump(settings, f)
        
        # Update DNS configuration
        dns_manager.update_user_dns(user_id)
        
        return redirect(url_for('routes.index'))
    
    # Get user settings
    settings = dns_manager.get_user_settings(user_id)
    user_dir = f'/workspaces/httpl/sdcard/blserver/conf/users/{user_id}'
    with open(f'{user_dir}/ip.txt', 'r') as f:
        ip = f.read().strip()
    
    return render_template('user.html', user_id=user_id, ip=ip, settings=settings)

@bp.route('/delete-dns/<user_id>', methods=['POST'])
def delete_dns(user_id):
    """Delete DNS for a user"""
    dns_manager.delete_user_dns(user_id)
    return redirect(url_for('routes.index'))
