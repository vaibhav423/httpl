from flask import Blueprint, render_template, request, jsonify
from .models import db, User, BlockedSite
from .utils import DNSManager, IPTablesManager

# Create blueprints
main = Blueprint('main', __name__)

# Main routes
@main.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@main.route('/users')
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@main.route('/api/users/<int:user_id>/block-site', methods=['POST'])
def block_site(user_id):
    data = request.get_json()
    domain = data.get('domain')
    
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    
    user = User.query.get_or_404(user_id)
    
    # Create new blocked site
    blocked_site = BlockedSite(domain=domain, user_id=user.id)
    db.session.add(blocked_site)
    db.session.commit()
    
    # Get all blocked domains for the user
    blocked_domains = [site.domain for site in user.blocked_sites if site.is_active]
    
    # Update DNS configuration
    dns_manager = DNSManager()
    dns_manager.create_dnsmasq_config(blocked_domains)
    dns_manager.stop_dnsmasq()
    dns_manager.start_dnsmasq()
    
    # Update iptables rules
    iptables_manager = IPTablesManager()
    iptables_manager.clear_rules()
    iptables_manager.add_dns_redirect_rules()
    iptables_manager.add_http_redirect_rules()
    
    return jsonify({'message': 'Site blocked successfully'})

@main.route('/api/users/<int:user_id>/unblock-site/<int:site_id>', methods=['POST'])
def unblock_site(user_id, site_id):
    user = User.query.get_or_404(user_id)
    blocked_site = BlockedSite.query.get_or_404(site_id)
    
    if blocked_site.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    blocked_site.is_active = False
    db.session.commit()
    
    # Get remaining blocked domains for the user
    blocked_domains = [site.domain for site in user.blocked_sites if site.is_active]
    
    # Update DNS configuration
    dns_manager = DNSManager()
    dns_manager.create_dnsmasq_config(blocked_domains)
    dns_manager.stop_dnsmasq()
    dns_manager.start_dnsmasq()
    
    return jsonify({'message': 'Site unblocked successfully'})

@main.route('/api/users/<int:user_id>/blocked-sites')
def get_blocked_sites(user_id):
    user = User.query.get_or_404(user_id)
    blocked_sites = [
        {
            'id': site.id,
            'domain': site.domain,
            'created_at': site.created_at.isoformat(),
            'is_active': site.is_active
        }
        for site in user.blocked_sites
        if site.is_active
    ]
    return jsonify(blocked_sites)
