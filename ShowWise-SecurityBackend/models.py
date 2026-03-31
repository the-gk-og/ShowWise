"""Security Backend Models"""
from datetime import datetime, timedelta
from extensions import db
from enum import Enum


class IPThreatLevel(Enum):
    """IP Threat Levels"""
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    QUARANTINED = "quarantined"
    BLOCKED = "blocked"


class IPBlockReason(Enum):
    """Reasons for IP blocking"""
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    MALICIOUS_PAYLOAD = "malicious_payload"
    KNOWN_SCANNER = "known_scanner"
    ABUSE_REPORT = "abuse_report"
    MANUAL_BLOCK = "manual_block"
    AUTO_QUARANTINE = "auto_quarantine"


class EventType(Enum):
    """Security Event Types"""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    RATE_LIMIT_HIT = "rate_limit_hit"
    MALICIOUS_PAYLOAD = "malicious_payload"
    SCANNER_DETECTED = "scanner_detected"
    IP_BLOCKED = "ip_blocked"
    IP_UNBLOCKED = "ip_unblocked"
    APPEAL_CREATED = "appeal_created"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_REJECTED = "appeal_rejected"
    ABUSE_REPORT = "abuse_report"
    QUARANTINE_TRIGGERED = "quarantine_triggered"
    QUARANTINE_RELEASED = "quarantine_released"
    FORM_SUBMISSION_BLOCKED = "form_submission_blocked"


class IPThreat(db.Model):
    """IP Threat Model - Central IP reputation tracking"""
    __tablename__ = 'ip_threats'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False, index=True)
    
    # Threat Status
    threat_level = db.Column(db.String(20), default=IPThreatLevel.CLEAN.value, nullable=False)
    threat_score = db.Column(db.Integer, default=0)  # 0-100
    
    # Blocking
    is_blocked = db.Column(db.Boolean, default=False)
    block_reason = db.Column(db.String(50))
    blocked_at = db.Column(db.DateTime)
    blocked_by = db.Column(db.String(255))  # username or 'auto'
    
    # Quarantine
    is_quarantined = db.Column(db.Boolean, default=False)
    quarantine_reason = db.Column(db.String(255))
    quarantined_at = db.Column(db.DateTime)
    quarantine_expiry = db.Column(db.DateTime)  # Auto-release date
    
    # Whitelist (trusted IPs)
    is_whitelisted = db.Column(db.Boolean, default=False)
    whitelist_reason = db.Column(db.String(255))
    whitelisted_at = db.Column(db.DateTime)
    whitelisted_by = db.Column(db.String(255))
    
    # Stats
    total_requests = db.Column(db.Integer, default=0)
    failed_attempts = db.Column(db.Integer, default=0)
    successful_attempts = db.Column(db.Integer, default=0)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Geographic/ISP Info
    country = db.Column(db.String(2))
    city = db.Column(db.String(100))
    isp = db.Column(db.String(255))
    is_datacenter = db.Column(db.Boolean, default=False)
    is_vpn = db.Column(db.Boolean, default=False)
    is_proxy = db.Column(db.Boolean, default=False)
    
    # Relationships
    events = db.relationship('SecurityEvent', backref='ip_threat', cascade='all, delete-orphan')
    appeals = db.relationship('IPAppeal', backref='ip_threat', cascade='all, delete-orphan')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<IPThreat {self.ip_address} - {self.threat_level}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'threat_level': self.threat_level,
            'threat_score': self.threat_score,
            'is_blocked': self.is_blocked,
            'block_reason': self.block_reason,
            'is_quarantined': self.is_quarantined,
            'quarantine_expiry': self.quarantine_expiry.isoformat() if self.quarantine_expiry else None,
            'is_whitelisted': self.is_whitelisted,
            'total_requests': self.total_requests,
            'failed_attempts': self.failed_attempts,
            'country': self.country,
            'city': self.city,
            'is_datacenter': self.is_datacenter,
            'is_vpn': self.is_vpn,
            'is_proxy': self.is_proxy,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
        }


class SecurityEvent(db.Model):
    """Security Event Log"""
    __tablename__ = 'security_events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    
    # IP Info
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    ip_threat_id = db.Column(db.Integer, db.ForeignKey('ip_threats.id'))
    
    # Event Details
    service = db.Column(db.String(50), nullable=False)  # 'home', 'main', 'backend'
    user_id = db.Column(db.String(255))
    username = db.Column(db.String(255))
    
    # Threat Details
    threat_description = db.Column(db.Text)
    threat_severity = db.Column(db.String(20))  # low, medium, high, critical
    payload = db.Column(db.Text)  # Malicious payload (if any)
    
    # Request Details
    endpoint = db.Column(db.String(255))
    method = db.Column(db.String(10))
    user_agent = db.Column(db.String(500))
    user_agent_hash = db.Column(db.String(64))
    
    # Response
    http_status = db.Column(db.Integer)
    action_taken = db.Column(db.String(255))  # Action taken by system
    
    # Metadata
    app_version = db.Column(db.String(50))
    cloudflare_ray = db.Column(db.String(50))  # Cloudflare Ray ID
    forwarded_for = db.Column(db.String(500))  # X-Forwarded-For chain
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<SecurityEvent {self.event_type} - {self.ip_address}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'ip_address': self.ip_address,
            'service': self.service,
            'username': self.username,
            'threat_description': self.threat_description,
            'threat_severity': self.threat_severity,
            'endpoint': self.endpoint,
            'method': self.method,
            'action_taken': self.action_taken,
            'http_status': self.http_status,
            'created_at': self.created_at.isoformat(),
        }


class IPAppeal(db.Model):
    """IP Appeal - For IP owners to appeal blocks/quarantines"""
    __tablename__ = 'ip_appeals'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_threat_id = db.Column(db.Integer, db.ForeignKey('ip_threats.id'), nullable=False)
    
    # Appeal Details
    contact_email = db.Column(db.String(255), nullable=False)
    contact_name = db.Column(db.String(255))
    organization = db.Column(db.String(255))
    
    # Appeal Content
    reason = db.Column(db.Text, nullable=False)  # Why they believe block is wrong
    justification = db.Column(db.Text)  # Additional justification
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_notes = db.Column(db.Text)
    reviewed_by = db.Column(db.String(255))
    
    # Lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)  # Auto-expire appeals after period
    
    def __repr__(self):
        return f'<IPAppeal {self.ip_threat.ip_address} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_threat.ip_address,
            'status': self.status,
            'reason': self.reason,
            'contact_email': self.contact_email,
            'organization': self.organization,
            'created_at': self.created_at.isoformat(),
            'admin_notes': self.admin_notes,
        }


class RateLimitCounter(db.Model):
    """Rate Limit Tracking per IP"""
    __tablename__ = 'rate_limit_counters'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    endpoint = db.Column(db.String(255), nullable=False)
    
    request_count = db.Column(db.Integer, default=0)
    window_start = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('ip_address', 'endpoint', name='uq_ip_endpoint'),
    )
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecurityAlert(db.Model):
    """Active Security Alerts"""
    __tablename__ = 'security_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    alert_type = db.Column(db.String(50), nullable=False)  # brute_force, scanner, etc
    
    alert_message = db.Column(db.Text)
    severity = db.Column(db.String(20))  # low, medium, high, critical
    
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.String(255))
    acknowledged_at = db.Column(db.DateTime)
    
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.String(255))
    resolved_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecurityDashboardUser(db.Model):
    """Admin users for Security Dashboard"""
    __tablename__ = 'security_dashboard_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(255), unique=True)
    
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
