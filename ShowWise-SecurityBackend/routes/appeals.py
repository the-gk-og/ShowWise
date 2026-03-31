"""IP Appeal Routes"""
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import IPAppeal, IPThreat
from datetime import datetime, timedelta
from functools import wraps
import re

appeals_bp = Blueprint('appeals', __name__)


def require_api_key(f):
    """Decorator to check API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('API_INTEGRATION_KEY'):
            return jsonify({'error': 'Invalid or missing API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


@appeals_bp.route('/submit', methods=['POST'])
def submit_appeal():
    """Submit an appeal for a blocked/quarantined IP"""
    data = request.get_json()
    
    ip_address = data.get('ip_address')
    contact_email = data.get('contact_email')
    contact_name = data.get('contact_name')
    organization = data.get('organization')
    reason = data.get('reason')
    
    # Validation
    if not all([ip_address, contact_email, reason]):
        return jsonify({'error': 'ip_address, contact_email, and reason required'}), 400
    
    # Validate email
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', contact_email):
        return jsonify({'error': 'Invalid email address'}), 400
    
    # Get IP threat
    threat = IPThreat.query.filter_by(ip_address=ip_address).first()
    if not threat:
        return jsonify({'error': 'IP not found in threat database'}), 404
    
    # Check if IP is actually blocked or quarantined
    if not threat.is_blocked and not threat.is_quarantined:
        return jsonify({'error': 'IP is not blocked or quarantined'}), 400
    
    # Check for existing pending appeal
    existing_appeal = IPAppeal.query.filter_by(
        ip_threat_id=threat.id,
        status='pending'
    ).first()
    
    if existing_appeal:
        return jsonify({'error': 'Pending appeal already exists for this IP'}), 400
    
    # Create appeal
    appeal = IPAppeal(
        ip_threat_id=threat.id,
        contact_email=contact_email,
        contact_name=contact_name,
        organization=organization,
        reason=reason,
        expires_at=datetime.utcnow() + timedelta(days=current_app.config.get('APPEAL_EXPIRY_DAYS', 30))
    )
    
    db.session.add(appeal)
    db.session.commit()
    
    return jsonify({
        'id': appeal.id,
        'status': 'submitted',
        'message': 'Your appeal has been submitted for review',
        'expires_at': appeal.expires_at.isoformat()
    }), 201


@appeals_bp.route('/<int:appeal_id>', methods=['GET'])
def get_appeal(appeal_id):
    """Get appeal status"""
    appeal = IPAppeal.query.get(appeal_id)
    if not appeal:
        return jsonify({'error': 'Appeal not found'}), 404
    
    # Check if expired
    if appeal.expires_at and appeal.expires_at < datetime.utcnow() and appeal.status == 'pending':
        appeal.status = 'expired'
        db.session.commit()
    
    return jsonify(appeal.to_dict()), 200


@appeals_bp.route('', methods=['GET'])
@require_api_key
def list_appeals():
    """List appeals (admin only)"""
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = IPAppeal.query
    
    if status:
        query = query.filter_by(status=status)
    
    total = query.count()
    appeals = query.order_by(IPAppeal.created_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        'total': total,
        'appeals': [a.to_dict() for a in appeals]
    }), 200


@appeals_bp.route('/<int:appeal_id>/approve', methods=['POST'])
@require_api_key
def approve_appeal(appeal_id):
    """Approve an appeal"""
    data = request.get_json()
    admin_email = data.get('admin_email', 'admin@security.local')
    admin_notes = data.get('admin_notes', '')
    
    appeal = IPAppeal.query.get(appeal_id)
    if not appeal:
        return jsonify({'error': 'Appeal not found'}), 404
    
    if appeal.status != 'pending':
        return jsonify({'error': f'Cannot approve appeal with status: {appeal.status}'}), 400
    
    # Approve appeal and unblock IP
    appeal.status = 'approved'
    appeal.reviewed_by = admin_email
    appeal.reviewed_at = datetime.utcnow()
    appeal.admin_notes = admin_notes
    
    # Update IP threat
    threat = appeal.ip_threat
    threat.is_blocked = False
    threat.block_reason = None
    threat.blocked_at = None
    threat.is_quarantined = False
    threat.quarantine_reason = None
    threat.quarantine_expiry = None
    threat.threat_level = 'clean'
    
    db.session.commit()
    
    return jsonify({
        'id': appeal.id,
        'status': 'approved',
        'ip_address': threat.ip_address,
        'action': 'IP unblocked'
    }), 200


@appeals_bp.route('/<int:appeal_id>/reject', methods=['POST'])
@require_api_key
def reject_appeal(appeal_id):
    """Reject an appeal"""
    data = request.get_json()
    admin_email = data.get('admin_email', 'admin@security.local')
    admin_notes = data.get('admin_notes', '')
    
    appeal = IPAppeal.query.get(appeal_id)
    if not appeal:
        return jsonify({'error': 'Appeal not found'}), 404
    
    if appeal.status != 'pending':
        return jsonify({'error': f'Cannot reject appeal with status: {appeal.status}'}), 400
    
    appeal.status = 'rejected'
    appeal.reviewed_by = admin_email
    appeal.reviewed_at = datetime.utcnow()
    appeal.admin_notes = admin_notes
    
    db.session.commit()
    
    return jsonify({
        'id': appeal.id,
        'status': 'rejected',
        'message': 'Appeal has been rejected'
    }), 200
