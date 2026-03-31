"""Security Events Routes"""
from flask import Blueprint, request, jsonify
from extensions import db
from models import SecurityEvent
from datetime import datetime, timedelta
from functools import wraps

events_bp = Blueprint('events', __name__)


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


@events_bp.route('/log', methods=['POST'])
@require_api_key
def log_event():
    """Log a security event"""
    data = request.get_json()
    
    event = SecurityEvent(
        event_type=data.get('event_type'),
        ip_address=data.get('ip_address'),
        service=data.get('service'),
        user_id=data.get('user_id'),
        username=data.get('username'),
        threat_description=data.get('threat_description'),
        threat_severity=data.get('threat_severity', 'low'),
        payload=data.get('payload'),
        endpoint=data.get('endpoint'),
        method=data.get('method'),
        user_agent=request.headers.get('User-Agent'),
        http_status=data.get('http_status'),
        action_taken=data.get('action_taken'),
        cloudflare_ray=request.headers.get('CF-Ray'),
        app_version=data.get('app_version'),
    )
    
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'id': event.id, 'status': 'logged'}), 201


@events_bp.route('/<int:event_id>', methods=['GET'])
@require_api_key
def get_event(event_id):
    """Get event details"""
    event = SecurityEvent.query.get(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    return jsonify(event.to_dict()), 200


@events_bp.route('', methods=['GET'])
@require_api_key
def list_events():
    """List security events with filtering"""
    ip_address = request.args.get('ip_address')
    event_type = request.args.get('event_type')
    severity = request.args.get('severity')
    service = request.args.get('service')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = SecurityEvent.query
    
    if ip_address:
        query = query.filter_by(ip_address=ip_address)
    if event_type:
        query = query.filter_by(event_type=event_type)
    if severity:
        query = query.filter_by(threat_severity=severity)
    if service:
        query = query.filter_by(service=service)
    
    total = query.count()
    events = query.order_by(SecurityEvent.created_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        'total': total,
        'limit': limit,
        'offset': offset,
        'events': [e.to_dict() for e in events]
    }), 200


@events_bp.route('/summary', methods=['GET'])
@require_api_key
def event_summary():
    """Get summary statistics for events"""
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = SecurityEvent.query.filter(SecurityEvent.created_at >= since)
    
    total_events = query.count()
    critical_events = query.filter_by(threat_severity='critical').count()
    high_events = query.filter_by(threat_severity='high').count()
    
    threat_types = {}
    for event in query.all():
        threat_types[event.event_type] = threat_types.get(event.event_type, 0) + 1
    
    unique_ips = query.with_entities(SecurityEvent.ip_address).distinct().count()
    
    return jsonify({
        'hours': hours,
        'total_events': total_events,
        'critical_count': critical_events,
        'high_count': high_events,
        'unique_ips': unique_ips,
        'threat_types': threat_types,
    }), 200
