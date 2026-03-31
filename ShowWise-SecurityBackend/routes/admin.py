"""Admin Routes"""
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import IPThreat, SecurityEvent, IPAppeal, SecurityDashboardUser
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.security import generate_password_hash
import secrets

admin_bp = Blueprint('admin', __name__)


def require_admin_key(f):
    """Decorator for admin operations"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-Admin-Key')
        if not api_key or api_key != current_app.config.get('ADMIN_API_KEY'):
            return jsonify({'error': 'Invalid or missing admin key'}), 401
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/ip/<ip_address>/block', methods=['POST'])
@require_admin_key
def admin_block_ip(ip_address):
    """Admin: Block an IP"""
    data = request.get_json()
    reason = data.get('reason', 'admin_block')
    admin_email = data.get('admin_email', 'admin')
    
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    threat.is_blocked = True
    threat.block_reason = reason
    threat.blocked_at = datetime.utcnow()
    threat.blocked_by = admin_email
    threat.threat_level = 'blocked'
    
    db.session.commit()
    
    return jsonify({
        'ip_address': ip_address,
        'status': 'blocked',
        'reason': reason
    }), 200


@admin_bp.route('/ip/<ip_address>/unblock', methods=['POST'])
@require_admin_key
def admin_unblock_ip(ip_address):
    """Admin: Unblock an IP"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        return jsonify({'error': 'IP not found'}), 404
    
    threat.is_blocked = False
    threat.block_reason = None
    threat.blocked_at = None
    threat.threat_level = 'clean'
    threat.threat_score = 0
    
    db.session.commit()
    
    return jsonify({
        'ip_address': ip_address,
        'status': 'unblocked'
    }), 200


@admin_bp.route('/ip/<ip_address>/whitelist', methods=['POST'])
@require_admin_key
def admin_whitelist_ip(ip_address):
    """Admin: Whitelist an IP"""
    data = request.get_json()
    reason = data.get('reason', 'admin_whitelist')
    admin_email = data.get('admin_email', 'admin')
    
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    threat.is_whitelisted = True
    threat.whitelist_reason = reason
    threat.whitelisted_at = datetime.utcnow()
    threat.whitelisted_by = admin_email
    threat.is_blocked = False
    threat.is_quarantined = False
    threat.threat_level = 'clean'
    threat.threat_score = 0
    
    db.session.commit()
    
    return jsonify({
        'ip_address': ip_address,
        'status': 'whitelisted'
    }), 200


@admin_bp.route('/ip/<ip_address>/reset', methods=['POST'])
@require_admin_key
def admin_reset_ip(ip_address):
    """Admin: Reset IP threat state"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        return jsonify({'error': 'IP not found'}), 404
    
    threat.threat_level = 'clean'
    threat.threat_score = 0
    threat.is_blocked = False
    threat.is_quarantined = False
    threat.is_whitelisted = False
    threat.failed_attempts = 0
    
    db.session.commit()
    
    return jsonify({'ip_address': ip_address, 'status': 'reset'}), 200


@admin_bp.route('/threats', methods=['GET'])
@require_admin_key
def list_threats():
    """Admin: List IP threats"""
    threat_level = request.args.get('threat_level')
    is_blocked = request.args.get('is_blocked', type=lambda x: x.lower() == 'true')
    is_quarantined = request.args.get('is_quarantined', type=lambda x: x.lower() == 'true')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = IPThreat.query
    
    if threat_level:
        query = query.filter_by(threat_level=threat_level)
    if is_blocked is not None:
        query = query.filter_by(is_blocked=is_blocked)
    if is_quarantined is not None:
        query = query.filter_by(is_quarantined=is_quarantined)
    
    total = query.count()
    threats = query.order_by(IPThreat.threat_score.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        'total': total,
        'threats': [t.to_dict() for t in threats]
    }), 200


@admin_bp.route('/blocked-list', methods=['GET'])
@require_admin_key
def get_blocked_list():
    """Admin: Get list of all blocked IPs for firewall rules"""
    blocked_ips = IPThreat.query.filter_by(is_blocked=True).all()
    
    return jsonify({
        'count': len(blocked_ips),
        'ips': [t.ip_address for t in blocked_ips],
        'detailed': [t.to_dict() for t in blocked_ips]
    }), 200


@admin_bp.route('/quarantine-list', methods=['GET'])
@require_admin_key
def get_quarantine_list():
    """Admin: Get list of all quarantined IPs"""
    quarantine_ips = IPThreat.query.filter_by(is_quarantined=True).all()
    
    now = datetime.utcnow()
    for ip_threat in quarantine_ips:
        if ip_threat.quarantine_expiry and ip_threat.quarantine_expiry < now:
            ip_threat.is_quarantined = False
            ip_threat.quarantine_expiry = None
    db.session.commit()
    
    return jsonify({
        'count': len(quarantine_ips),
        'ips': [t.ip_address for t in quarantine_ips],
        'detailed': [t.to_dict() for t in quarantine_ips]
    }), 200


@admin_bp.route('/bulk-action', methods=['POST'])
@require_admin_key
def bulk_action():
    """Admin: Perform bulk action on IPs"""
    data = request.get_json()
    action = data.get('action')  # block, unblock, whitelist, quarantine, reset
    ips = data.get('ips', [])  # List of IP addresses
    reason = data.get('reason', '')
    admin_email = data.get('admin_email', 'admin')
    
    if not action or not ips:
        return jsonify({'error': 'action and ips required'}), 400
    
    affected = 0
    
    if action == 'block':
        for ip in ips:
            threat = IPThreat.query.filter_by(ip_address=ip).first()
            if not threat:
                threat = IPThreat(ip_address=ip)
                db.session.add(threat)
            threat.is_blocked = True
            threat.block_reason = reason or 'bulk_block'
            threat.blocked_at = datetime.utcnow()
            threat.blocked_by = admin_email
            affected += 1
    
    elif action == 'unblock':
        for ip in ips:
            threat = IPThreat.query.filter_by(ip_address=ip).first()
            if threat:
                threat.is_blocked = False
                threat.block_reason = None
                affected += 1
    
    elif action == 'whitelist':
        for ip in ips:
            threat = IPThreat.query.filter_by(ip_address=ip).first()
            if not threat:
                threat = IPThreat(ip_address=ip)
                db.session.add(threat)
            threat.is_whitelisted = True
            threat.whitelist_reason = reason or 'bulk_whitelist'
            threat.whitelisted_at = datetime.utcnow()
            threat.whitelisted_by = admin_email
            affected += 1
    
    elif action == 'reset':
        for ip in ips:
            threat = IPThreat.query.filter_by(ip_address=ip).first()
            if threat:
                threat.threat_level = 'clean'
                threat.threat_score = 0
                threat.is_blocked = False
                threat.is_quarantined = False
                threat.is_whitelisted = False
                affected += 1
    
    db.session.commit()
    
    return jsonify({
        'action': action,
        'affected': affected,
        'status': 'completed'
    }), 200


@admin_bp.route('/stats', methods=['GET'])
@require_admin_key
def get_stats():
    """Admin: Get security statistics"""
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    total_ips = IPThreat.query.count()
    blocked_ips = IPThreat.query.filter_by(is_blocked=True).count()
    quarantined_ips = IPThreat.query.filter_by(is_quarantined=True).count()
    whitelisted_ips = IPThreat.query.filter_by(is_whitelisted=True).count()
    
    recent_events = SecurityEvent.query.filter(SecurityEvent.created_at >= since).count()
    critical_events = SecurityEvent.query.filter(
        SecurityEvent.created_at >= since,
        SecurityEvent.threat_severity == 'critical'
    ).count()
    
    pending_appeals = IPAppeal.query.filter_by(status='pending').count()
    
    return jsonify({
        'ips': {
            'total': total_ips,
            'blocked': blocked_ips,
            'quarantined': quarantined_ips,
            'whitelisted': whitelisted_ips,
        },
        'events': {
            'recent': recent_events,
            'critical': critical_events,
            'time_window_hours': hours,
        },
        'appeals': {
            'pending': pending_appeals,
        }
    }), 200


@admin_bp.route('/user/create', methods=['POST'])
@require_admin_key
def create_admin_user():
    """Admin: Create dashboard user"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    is_admin = data.get('is_admin', False)
    
    if not all([username, email, password]):
        return jsonify({'error': 'username, email, password required'}), 400
    
    if SecurityDashboardUser.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = SecurityDashboardUser(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        api_key=secrets.token_urlsafe(32),
        is_admin=is_admin,
        is_active=True
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'id': user.id,
        'username': username,
        'email': email,
        'api_key': user.api_key,
        'is_admin': is_admin
    }), 201
