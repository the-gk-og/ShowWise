"""IP Service - Business logic for IP management"""
from extensions import db
from models import IPThreat, SecurityEvent
from datetime import datetime, timedelta


def check_ip_status(ip_address):
    """Check IP status and return detailed info"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        return {
            'ip_address': ip_address,
            'status': 'unknown',
            'is_blocked': False,
            'is_quarantined': False,
            'can_access': True,
        }
    
    # Check if quarantine expired
    if threat.is_quarantined and threat.quarantine_expiry:
        if threat.quarantine_expiry < datetime.utcnow():
            threat.is_quarantined = False
            threat.quarantine_expiry = None
            db.session.commit()
    
    can_access = not threat.is_blocked and not threat.is_quarantined
    
    return {
        'ip_address': ip_address,
        'status': threat.threat_level,
        'is_blocked': threat.is_blocked,
        'is_quarantined': threat.is_quarantined,
        'can_access': can_access,
        'threat_score': threat.threat_score,
        'block_reason': threat.block_reason,
        'quarantine_reason': threat.quarantine_reason,
    }


def block_ip(ip_address, reason='manual_block', blocked_by='api'):
    """Block an IP address"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    threat.is_blocked = True
    threat.block_reason = reason
    threat.blocked_at = datetime.utcnow()
    threat.blocked_by = blocked_by
    threat.threat_level = 'blocked'
    threat.threat_score = 100
    threat.is_quarantined = False  # Remove quarantine if applied
    threat.quarantine_expiry = None
    
    db.session.commit()
    
    return {
        'ip_address': ip_address,
        'action': 'blocked',
        'reason': reason,
        'blocked_at': threat.blocked_at.isoformat(),
    }


def unblock_ip(ip_address, reason='manual_unblock'):
    """Unblock an IP address"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        return {'error': 'IP not found'}
    
    threat.is_blocked = False
    threat.block_reason = None
    threat.blocked_at = None
    threat.threat_level = 'clean'
    threat.threat_score = 0
    
    db.session.commit()
    
    return {
        'ip_address': ip_address,
        'action': 'unblocked',
        'reason': reason,
    }


def quarantine_ip(ip_address, reason='suspicious_activity', days=7):
    """Quarantine an IP for specified days"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    threat.is_quarantined = True
    threat.quarantine_reason = reason
    threat.quarantined_at = datetime.utcnow()
    threat.quarantine_expiry = datetime.utcnow() + timedelta(days=days)
    threat.threat_level = 'quarantined'
    
    db.session.commit()
    
    return {
        'ip_address': ip_address,
        'action': 'quarantined',
        'reason': reason,
        'expiry': threat.quarantine_expiry.isoformat(),
    }


def release_ip(ip_address):
    """Release a quarantined IP"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        return {'error': 'IP not found'}
    
    threat.is_quarantined = False
    threat.quarantine_reason = None
    threat.quarantine_expiry = None
    threat.threat_level = 'clean'
    threat.threat_score = max(0, threat.threat_score - 10)
    
    db.session.commit()
    
    return {
        'ip_address': ip_address,
        'action': 'released',
    }


def whitelist_ip(ip_address, reason='whitelisted', whitelisted_by='api'):
    """Whitelist a trusted IP"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    threat.is_whitelisted = True
    threat.whitelist_reason = reason
    threat.whitelisted_at = datetime.utcnow()
    threat.whitelisted_by = whitelisted_by
    threat.is_blocked = False
    threat.is_quarantined = False
    threat.threat_level = 'clean'
    threat.threat_score = 0
    
    db.session.commit()
    
    return {
        'ip_address': ip_address,
        'action': 'whitelisted',
        'reason': reason,
    }


def update_ip_threat_level(ip_address, threat_type, severity='medium'):
    """Update threat level based on incident type"""
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    
    if not threat:
        threat = IPThreat(ip_address=ip_address)
        db.session.add(threat)
    
    # Map severity to threat score increase
    severity_map = {
        'low': 5,
        'medium': 15,
        'high': 30,
        'critical': 50,
    }
    
    increase = severity_map.get(severity, 15)
    threat.threat_score = min(100, threat.threat_score + increase)
    
    # Update threat level based on score
    if threat.threat_score >= 80:
        threat.threat_level = 'blocked'
    elif threat.threat_score >= 50:
        threat.threat_level = 'quarantined'
    elif threat.threat_score >= 20:
        threat.threat_level = 'suspicious'
    else:
        threat.threat_level = 'clean'
    
    db.session.commit()
    
    return threat.to_dict()
