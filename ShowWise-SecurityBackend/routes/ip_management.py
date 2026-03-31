"""IP Management Routes - Core IP threat management"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import IPThreat, SecurityEvent, EventType, IPBlockReason
from datetime import datetime, timedelta
from services.ip_service import (
    check_ip_status, block_ip, unblock_ip, quarantine_ip,
    release_ip, whitelist_ip, update_ip_threat_level
)
from functools import wraps

ip_bp = Blueprint('ip', __name__)


def require_api_key(f):
    """Decorator to check API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import current_app
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('API_INTEGRATION_KEY'):
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


@ip_bp.route('/status/<ip_address>', methods=['GET'])
@require_api_key
def get_ip_status(ip_address):
    """Get IP status and threat information"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        return jsonify({'ip_address': ip_address, 'threat_level': 'clean', 'status': 'unknown'}), 200
    
    return jsonify(threat.to_dict()), 200


@ip_bp.route('/check', methods=['POST'])
@require_api_key
def check_ip():
    """Check and log security event for IP"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    event_type = data.get('event_type', EventType.LOGIN_ATTEMPT.value)
    service = data.get('service', 'unknown')
    
    if not ip_address:
        return jsonify({'error': 'ip_address required'}), 400
    
    # Get or create threat record
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
        db.session.commit()
    
    # Update last seen
    threat.last_seen = datetime.utcnow()
    threat.total_requests += 1
    
    # Log event
    event = SecurityEvent(
        event_type=event_type,
        ip_address=ip_address,
        ip_threat_id=threat.id,
        service=service,
        user_agent=request.headers.get('User-Agent'),
        endpoint=request.endpoint,
        method=request.method,
        user_id=data.get('user_id'),
        username=data.get('username'),
        cloudflare_ray=request.headers.get('CF-Ray'),
    )
    db.session.add(event)
    
    # Check if blocked or quarantined
    can_proceed = True
    reason = None
    
    if threat.is_blocked:
        can_proceed = False
        reason = f'IP is blocked: {threat.block_reason}'
    elif threat.is_quarantined:
        if threat.quarantine_expiry and threat.quarantine_expiry < datetime.utcnow():
            threat.is_quarantined = False
            threat.quarantine_expiry = None
        else:
            can_proceed = False
            reason = f'IP is quarantined: {threat.quarantine_reason}'
    
    db.session.commit()
    
    return jsonify({
        'ip_address': ip_address,
        'can_proceed': can_proceed,
        'reason': reason,
        'threat_level': threat.threat_level,
        'threat_score': threat.threat_score,
    }), 200


@ip_bp.route('/report-threat', methods=['POST'])
@require_api_key
def report_threat():
    """Report a threat from a service"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    threat_type = data.get('threat_type')  # malicious_payload, scanner, brute_force, etc
    severity = data.get('severity', 'medium')  # low, medium, high, critical
    description = data.get('description')
    payload = data.get('payload')
    service = data.get('service')
    
    if not ip_address or not threat_type:
        return jsonify({'error': 'ip_address and threat_type required'}), 400
    
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    # Increase threat score
    threat_increase = {'low': 10, 'medium': 25, 'high': 50, 'critical': 100}.get(severity, 25)
    threat.threat_score = min(100, threat.threat_score + threat_increase)
    
    # Decide threat level
    if threat.threat_score >= 80:
        threat.threat_level = 'blocked'
    elif threat.threat_score >= 50:
        threat.threat_level = 'quarantined'
    elif threat.threat_score >= 20:
        threat.threat_level = 'suspicious'
    
    # Log the event
    event = SecurityEvent(
        event_type=f'threat_reported_{threat_type}',
        ip_address=ip_address,
        ip_threat_id=threat.id,
        service=service,
        threat_severity=severity,
        threat_description=description,
        payload=payload,
        user_agent=request.headers.get('User-Agent'),
        cloudflare_ray=request.headers.get('CF-Ray'),
    )
    db.session.add(event)
    
    # Auto-block if critical
    if severity == 'critical' or threat.threat_score >= 80:
        threat.is_blocked = True
        threat.block_reason = f'{threat_type} (auto-blocked)'
        threat.blocked_at = datetime.utcnow()
        threat.blocked_by = 'auto'
    elif severity == 'high' or threat.threat_score >= 50:
        threat.is_quarantined = True
        threat.quarantine_reason = f'{threat_type} (auto-quarantined)'
        threat.quarantined_at = datetime.utcnow()
        threat.quarantine_expiry = datetime.utcnow() + timedelta(days=7)
    
    db.session.commit()
    
    return jsonify({
        'ip_address': ip_address,
        'threat_level': threat.threat_level,
        'threat_score': threat.threat_score,
        'action_taken': 'blocked' if threat.is_blocked else 'quarantined' if threat.is_quarantined else 'logged'
    }), 201


@ip_bp.route('/rate-limit', methods=['POST'])
@require_api_key
def report_rate_limit():
    """Report rate limit hit from service"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    
    if not ip_address:
        return jsonify({'error': 'ip_address required'}), 400
    
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    threat.threat_score = min(100, threat.threat_score + 5)
    threat.failed_attempts += 1
    
    # Log event
    event = SecurityEvent(
        event_type=EventType.RATE_LIMIT_HIT.value,
        ip_address=ip_address,
        ip_threat_id=threat.id,
        service=data.get('service'),
        threat_severity='low',
        cloudflare_ray=request.headers.get('CF-Ray'),
    )
    db.session.add(event)
    
    # Auto-quarantine if too many rate limit hits
    if threat.failed_attempts >= 10:
        if not threat.is_quarantined and not threat.is_blocked:
            threat.is_quarantined = True
            threat.quarantine_reason = 'Excessive rate limit violations'
            threat.quarantined_at = datetime.utcnow()
            threat.quarantine_expiry = datetime.utcnow() + timedelta(hours=24)
    
    db.session.commit()
    
    return jsonify({
        'ip_address': ip_address,
        'threat_score': threat.threat_score,
        'quarantined': threat.is_quarantined
    }), 200


@ip_bp.route('/block', methods=['POST'])
@require_api_key
def block_ip_endpoint():
    """Manually block an IP"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    reason = data.get('reason', 'manual_block')
    blocked_by = data.get('blocked_by', 'api')
    
    if not ip_address:
        return jsonify({'error': 'ip_address required'}), 400
    
    result = block_ip(ip_address, reason, blocked_by)
    return jsonify(result), 200


@ip_bp.route('/unblock', methods=['POST'])
@require_api_key
def unblock_ip_endpoint():
    """Unblock an IP"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    reason = data.get('reason', 'manual_unblock')
    
    if not ip_address:
        return jsonify({'error': 'ip_address required'}), 400
    
    result = unblock_ip(ip_address, reason)
    return jsonify(result), 200


@ip_bp.route('/whitelist', methods=['POST'])
@require_api_key
def whitelist_ip_endpoint():
    """Whitelist an IP (trusted)"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    reason = data.get('reason', 'whitelisted')
    whitelisted_by = data.get('whitelisted_by', 'api')
    
    if not ip_address:
        return jsonify({'error': 'ip_address required'}), 400
    
    result = whitelist_ip(ip_address, reason, whitelisted_by)
    return jsonify(result), 200


@ip_bp.route('/quarantine', methods=['POST'])
@require_api_key
def quarantine_ip_endpoint():
    """Quarantine an IP"""
    data = request.get_json()
    ip_address = data.get('ip_address')
    reason = data.get('reason', 'suspicious_activity')
    days = data.get('quarantine_days', 7)
    
    if not ip_address:
        return jsonify({'error': 'ip_address required'}), 400
    
    result = quarantine_ip(ip_address, reason, days)
    return jsonify(result), 200


@ip_bp.route('/<ip_address>/history', methods=['GET'])
@require_api_key
def get_ip_history(ip_address):
    """Get activity history for an IP"""
    limit = request.args.get('limit', 50, type=int)
    events = SecurityEvent.query.filter_by(ip_address=ip_address).order_by(
        SecurityEvent.created_at.desc()
    ).limit(limit).all()
    
    return jsonify({
        'ip_address': ip_address,
        'events': [e.to_dict() for e in events]
    }), 200
