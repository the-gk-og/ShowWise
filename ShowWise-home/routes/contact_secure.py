"""ShowWise-home Security Integration"""
from flask import Blueprint, request, jsonify, render_template_string
from services.security.security_utils import (
    get_client_ip, detect_malicious_patterns, sanitize_input,
    validate_email, check_ip_blocked, report_to_security_backend,
    log_security_event, detect_scanner_user_agent, ThreatLevel
)
from services.security.cloudflare_integration import CloudflareIntegration
from services.security.validation_chain import validate_and_sanitize
from services.security.middleware import security_middleware, block_malicious_payload
from services.email_service import send_email
from extensions import db
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

contact_bp = Blueprint('contact', __name__, url_prefix='/contact')

# Initialize rate limiter
limiter = Limiter(
    key_func=lambda: get_client_ip(),
    storage_uri='memory://',
    default_limits=["5 per minute"],
)


@contact_bp.route('/form', methods=['GET'])
@security_middleware
def contact_form():
    """Display contact form with Turnstile CAPTCHA"""
    turnstile_site_key = 'get_from_config'  # Placeholder
    
    form_html = '''
    <form id="contact-form" method="POST" action="/contact/submit">
        <div class="form-group">
            <label>Name:</label>
            <input type="text" name="name" required>
        </div>
        <div class="form-group">
            <label>Email:</label>
            <input type="email" name="email" required>
        </div>
        <div class="form-group">
            <label>Message:</label>
            <textarea name="message" required></textarea>
        </div>
        <div class="cf-turnstile" data-sitekey="''' + turnstile_site_key + '''"></div>
        <button type="submit">Send</button>
    </form>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
    '''
    return form_html


@contact_bp.route('/submit', methods=['POST'])
@limiter.limit("5 per minute")
@security_middleware
@block_malicious_payload
def submit_contact():
    """Handle contact form submission with security checks"""
    
    ip_address = get_client_ip()
    
    # Check if IP is blocked
    is_blocked, block_reason = check_ip_blocked(ip_address)
    if is_blocked:
        log_security_event(
            'contact_form_blocked',
            ip_address=ip_address,
            severity=ThreatLevel.MEDIUM.value,
            description=f'Blocked IP tried to submit contact form: {block_reason}'
        )
        return jsonify({
            'error': 'Your IP is blocked from submitting forms',
            'code': 'IP_BLOCKED'
        }), 403
    
    # Get form data
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        turnstile_token = request.form.get('cf-turnstile-response', '').strip()
    except Exception as e:
        return jsonify({'error': 'Invalid request format'}), 400
    
    # Validate turnstile token
    is_human, turnstile_msg = CloudflareIntegration.verify_turnstile_token(turnstile_token)
    if not is_human:
        report_to_security_backend(
            'turnstile_verification_failed',
            ip_address,
            threat_type='failed_captcha',
            severity='low',
            description=turnstile_msg
        )
        return jsonify({
            'error': 'CAPTCHA verification failed',
            'code': 'CAPTCHA_FAILED'
        }), 400
    
    # Validate and sanitize inputs
    name_sanitized, name_errors = validate_and_sanitize('username', name)
    if name_errors:
        log_security_event(
            'contact_form_validation_failed',
            ip_address=ip_address,
            severity=ThreatLevel.LOW.value,
            description=f'Name validation failed: {name_errors}'
        )
        return jsonify({'error': 'Invalid name format', 'details': name_errors}), 400
    
    email_sanitized, email_errors = validate_and_sanitize('email', email)
    if email_errors:
        log_security_event(
            'contact_form_validation_failed',
            ip_address=ip_address,
            severity=ThreatLevel.LOW.value,
            description=f'Email validation failed: {email_errors}'
        )
        return jsonify({'error': 'Invalid email format', 'details': email_errors}), 400
    
    message_sanitized, message_errors = validate_and_sanitize('message', message)
    if message_errors:
        log_security_event(
            'contact_form_validation_failed',
            ip_address=ip_address,
            severity=ThreatLevel.LOW.value,
            description=f'Message validation failed: {message_errors}'
        )
        return jsonify({'error': 'Invalid message format', 'details': message_errors}), 400
    
    # Send email
    try:
        email_sent = send_email(
            subject='New Contact Form Submission',
            recipients=['admin@showwise.local'],
            text_body=f'Name: {name_sanitized}\nEmail: {email_sanitized}\n\nMessage:\n{message_sanitized}',
            html_body=f'<p><strong>Name:</strong> {name_sanitized}</p><p><strong>Email:</strong> {email_sanitized}</p><p><strong>Message:</strong><br>{message_sanitized}</p>'
        )
        
        if email_sent:
            log_security_event(
                'contact_form_submitted',
                ip_address=ip_address,
                severity=ThreatLevel.LOW.value,
                description=f'Contact form submitted successfully from {email_sanitized}'
            )
            return jsonify({
                'success': True,
                'message': 'Thank you for your message. We will get back to you soon.'
            }), 200
        else:
            return jsonify({'error': 'Failed to send email'}), 500
    
    except Exception as e:
        log_security_event(
            'contact_form_error',
            ip_address=ip_address,
            severity=ThreatLevel.MEDIUM.value,
            description=f'Error processing contact form: {str(e)}'
        )
        return jsonify({'error': 'Internal server error'}), 500


@contact_bp.route('/quote', methods=['POST'])
@limiter.limit("3 per minute")
@security_middleware
@block_malicious_payload
def submit_quote():
    """Handle quote request with security"""
    ip_address = get_client_ip()
    
    is_blocked, _ = check_ip_blocked(ip_address)
    if is_blocked:
        return jsonify({'error': 'Your IP is blocked'}), 403
    
    # Verify Turnstile
    turnstile_token = request.form.get('cf-turnstile-response', '')
    is_human, _ = CloudflareIntegration.verify_turnstile_token(turnstile_token)
    if not is_human:
        report_to_security_backend('quote_captcha_failed', ip_address, 'failed_captcha', 'low')
        return jsonify({'error': 'CAPTCHA verification failed'}), 400
    
    # Process quote request
    try:
        company = request.form.get('company', '').strip()
        email = request.form.get('email', '').strip()
        description = request.form.get('description', '').strip()
        
        # Sanitize
        company_clean = sanitize_input(company)
        email_clean = sanitize_input(email)
        description_clean = sanitize_input(description)
        
        # Validate
        if not validate_email(email_clean):
            return jsonify({'error': 'Invalid email'}), 400
        
        # Send to admin
        send_email(
            subject=f'New Quote Request from {company_clean}',
            recipients=['admin@showwise.local'],
            text_body=f'Company: {company_clean}\nEmail: {email_clean}\n\nDescription:\n{description_clean}'
        )
        
        log_security_event('quote_request_submitted', ip_address, severity='low')
        return jsonify({'success': True, 'message': 'Quote request submitted'}), 200
    
    except Exception as e:
        log_security_event('quote_error', ip_address, severity='medium', description=str(e))
        return jsonify({'error': 'Internal error'}), 500


def register_contact_routes(app):
    """Register contact routes to app"""
    app.register_blueprint(contact_bp)
