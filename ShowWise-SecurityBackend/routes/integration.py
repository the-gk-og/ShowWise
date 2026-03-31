"""Cross-Service Integration Routes"""
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import IPThreat, SecurityEvent
from datetime import datetime
from functools import wraps
import hmac
import hashlib

integration_bp = Blueprint('integration', __name__)


def verify_hmac_signature(data, signature, secret):
    """Verify HMAC signature of request"""
    computed_signature = hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature)


def require_integration_signature(f):
    """Verify cross-service HMAC signature"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        
        signature = request.headers.get('X-Integration-Signature')
        service = request.headers.get('X-Service-ID')
        
        if not signature or not service:
            return jsonify({'error': 'Missing signature or service ID'}), 401
        
        secret = current_app.config.get('API_INTEGRATION_SECRET')
        data = request.get_data(as_text=True)
        
        if not verify_hmac_signature(data, signature, secret):
            return jsonify({'error': 'Invalid signature'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


@integration_bp.route('/check-ip', methods=['POST'])
@require_integration_signature
def check_ip():
    """Cross-service IP check endpoint"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    
    if not ip_address:
        return jsonify({'error': 'ip_address required'}), 400
    
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        return jsonify({
            'ip_address': ip_address,
            'status': 'unknown',
            'can_access': True,
        }), 200
    
    can_access = not threat.is_blocked and not threat.is_quarantined
    
    return jsonify({
        'ip_address': ip_address,
        'status': threat.threat_level,
        'can_access': can_access,
        'threat_score': threat.threat_score,
        'reason': threat.block_reason or threat.quarantine_reason,
    }), 200


@integration_bp.route('/report-ip-activity', methods=['POST'])
@require_integration_signature
def report_ip_activity():
    """Cross-service IP activity reporting"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    activity_type = data.get('activity_type')  # success, failure, suspicious, etc
    service = request.headers.get('X-Service-ID', 'unknown')
    
    if not ip_address or not activity_type:
        return jsonify({'error': 'ip_address and activity_type required'}), 400
    
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    # Update stats
    threat.last_seen = datetime.utcnow()
    threat.total_requests += 1
    
    if activity_type == 'success':
        threat.successful_attempts += 1
    elif activity_type in ['failure', 'suspicious']:
        threat.failed_attempts += 1
        threat.threat_score = min(100, threat.threat_score + 5)
    
    db.session.commit()
    
    return jsonify({
        'ip_address': ip_address,
        'status': 'recorded',
    }), 200


@integration_bp.route('/get-blocked-ips', methods=['GET'])
@require_integration_signature
def get_blocked_ips():
    """Get blocklist for other services"""
    service = request.headers.get('X-Service-ID', 'unknown')
    
    blocked = IPThreat.query.filter_by(is_blocked=True).all()
    quarantined = IPThreat.query.filter(
        IPThreat.is_quarantined == True,
        IPThreat.quarantine_expiry > datetime.utcnow()
    ).all()
    
    return jsonify({
        'blocked_count': len(blocked),
        'quarantined_count': len(quarantined),
        'blocked_ips': [t.ip_address for t in blocked],
        'quarantined_ips': [t.ip_address for t in quarantined],
    }), 200


@integration_bp.route('/sync-threat', methods=['POST'])
@require_integration_signature
def sync_threat():
    """Sync threat data across services"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    threat_data = data.get('threat_data', {})
    service = request.headers.get('X-Service-ID', 'unknown')
    
    if not ip_address:
        return jsonify({'error': 'ip_address required'}), 400
    
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    # Update threat data if provided
    if 'country' in threat_data:
        threat.country = threat_data['country']
    if 'city' in threat_data:
        threat.city = threat_data['city']
    if 'is_datacenter' in threat_data:
        threat.is_datacenter = threat_data['is_datacenter']
    if 'is_vpn' in threat_data:
        threat.is_vpn = threat_data['is_vpn']
    if 'is_proxy' in threat_data:
        threat.is_proxy = threat_data['is_proxy']
    
    db.session.commit()
    
    return jsonify({
        'ip_address': ip_address,
        'status': 'synced',
        'service': service,
    }), 200
