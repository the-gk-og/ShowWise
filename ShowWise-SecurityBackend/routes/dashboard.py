"""Dashboard Routes - Security Dashboard API"""
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import IPThreat, SecurityEvent, IPAppeal, SecurityAlert
from datetime import datetime, timedelta
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__)


def require_api_key(f):
    """Decorator to check API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('API_INTEGRATION_KEY'):
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


@dashboard_bp.route('/overview', methods=['GET'])
@require_api_key
def get_overview():
    """Get security dashboard overview"""
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # IP statistics
    total_ips = IPThreat.query.count()
    blocked_count = IPThreat.query.filter_by(is_blocked=True).count()
    quarantined_count = IPThreat.query.filter_by(is_quarantined=True).count()
    whitelisted_count = IPThreat.query.filter_by(is_whitelisted=True).count()
    
    # Event statistics
    total_events = SecurityEvent.query.filter(SecurityEvent.created_at >= since).count()
    critical_events = SecurityEvent.query.filter(
        SecurityEvent.created_at >= since,
        SecurityEvent.threat_severity == 'critical'
    ).count()
    high_events = SecurityEvent.query.filter(
        SecurityEvent.created_at >= since,
        SecurityEvent.threat_severity == 'high'
    ).count()
    
    # Threat statistics
    threat_ips = IPThreat.query.filter(IPThreat.threat_score > 50).count()
    
    # Appeal statistics
    pending_appeals = IPAppeal.query.filter_by(status='pending').count()
    
    # Alert statistics
    unresolved_alerts = SecurityAlert.query.filter_by(is_resolved=False).count()
    
    return jsonify({
        'overview': {
            'timestamp': datetime.utcnow().isoformat(),
            'time_window_hours': hours,
        },
        'ips': {
            'total': total_ips,
            'blocked': blocked_count,
            'quarantined': quarantined_count,
            'whitelisted': whitelisted_count,
            'suspicious': threat_ips,
        },
        'events': {
            'total': total_events,
            'critical': critical_events,
            'high': high_events,
        },
        'appeals': {
            'pending': pending_appeals,
        },
        'alerts': {
            'unresolved': unresolved_alerts,
        }
    }), 200


@dashboard_bp.route('/top-ips', methods=['GET'])
@require_api_key
def get_top_ips():
    """Get top threat IPs"""
    limit = request.args.get('limit', 20, type=int)
    
    threats = IPThreat.query.order_by(IPThreat.threat_score.desc()).limit(limit).all()
    
    return jsonify({
        'count': len(threats),
        'ips': [t.to_dict() for t in threats]
    }), 200


@dashboard_bp.route('/recent-events', methods=['GET'])
@require_api_key
def get_recent_events():
    """Get recent security events"""
    limit = request.args.get('limit', 50, type=int)
    severity = request.args.get('severity')
    
    query = SecurityEvent.query
    if severity:
        query = query.filter_by(threat_severity=severity)
    
    events = query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'count': len(events),
        'events': [e.to_dict() for e in events]
    }), 200


@dashboard_bp.route('/threat-timeline', methods=['GET'])
@require_api_key
def get_threat_timeline():
    """Get threat activity timeline"""
    days = request.args.get('days', 7, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    events = SecurityEvent.query.filter(
        SecurityEvent.created_at >= since
    ).order_by(SecurityEvent.created_at).all()
    
    # Group by day
    timeline = {}
    for event in events:
        day = event.created_at.strftime('%Y-%m-%d')
        if day not in timeline:
            timeline[day] = {
                'total': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
            }
        timeline[day]['total'] += 1
        timeline[day][event.threat_severity if event.threat_severity else 'low'] += 1
    
    return jsonify(timeline), 200


@dashboard_bp.route('/threat-distribution', methods=['GET'])
@require_api_key
def get_threat_distribution():
    """Get threat distribution by type/country/service"""
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    events = SecurityEvent.query.filter(SecurityEvent.created_at >= since).all()
    
    # By event type
    by_type = {}
    by_service = {}
    by_country = {}
    
    for event in events:
        by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
        by_service[event.service] = by_service.get(event.service, 0) + 1
    
    # By country (from IP threats)
    threats = IPThreat.query.filter(IPThreat.updated_at >= since).all()
    for threat in threats:
        if threat.country:
            by_country[threat.country] = by_country.get(threat.country, 0) + 1
    
    return jsonify({
        'by_type': by_type,
        'by_service': by_service,
        'by_country': by_country,
    }), 200


@dashboard_bp.route('/critical-alerts', methods=['GET'])
@require_api_key
def get_critical_alerts():
    """Get critical active alerts"""
    alerts = SecurityAlert.query.filter(
        SecurityAlert.is_resolved == False,
        SecurityAlert.severity.in_(['critical', 'high'])
    ).order_by(SecurityAlert.created_at.desc()).all()
    
    return jsonify({
        'count': len(alerts),
        'alerts': [{
            'id': a.id,
            'ip_address': a.ip_address,
            'alert_type': a.alert_type,
            'message': a.alert_message,
            'severity': a.severity,
            'created_at': a.created_at.isoformat(),
        } for a in alerts]
    }), 200


@dashboard_bp.route('/pending-appeals', methods=['GET'])
@require_api_key
def get_pending_appeals():
    """Get pending IP appeals"""
    appeals = IPAppeal.query.filter_by(status='pending').order_by(
        IPAppeal.created_at.asc()
    ).all()
    
    return jsonify({
        'count': len(appeals),
        'appeals': [a.to_dict() for a in appeals]
    }), 200


@dashboard_bp.route('/statistics', methods=['GET'])
@require_api_key
def get_statistics():
    """Get comprehensive statistics"""
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    
    # Event statistics
    events = SecurityEvent.query.filter(SecurityEvent.created_at >= since)
    total_events = events.count()
    unique_ips = events.with_entities(SecurityEvent.ip_address).distinct().count()
    unique_services = events.with_entities(SecurityEvent.service).distinct().count()
    
    # Threat score average
    threats = IPThreat.query.filter(IPThreat.updated_at >= since)
    avg_threat_score = db.session.query(db.func.avg(IPThreat.threat_score)).scalar() or 0
    
    # Daily stats
    daily_events = {}
    for event in events.all():
        day = event.created_at.strftime('%Y-%m-%d')
        daily_events[day] = daily_events.get(day, 0) + 1
    
    return jsonify({
        'period_days': days,
        'events': {
            'total': total_events,
            'unique_ips': unique_ips,
            'unique_services': unique_services,
        },
        'threats': {
            'avg_threat_score': round(float(avg_threat_score), 2),
        },
        'daily_breakdown': daily_events,
    }), 200
