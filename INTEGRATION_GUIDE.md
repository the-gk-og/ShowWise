# Integration Guide - Adding Security to Existing Routes

## Step 1: Import Security Modules

In your route file (e.g., `routes/auth.py`):

```python
from services.security.security_utils import (
    get_client_ip, check_ip_blocked, log_security_event,
    validate_email, ThreatLevel
)
from services.security.middleware import showwise_security_middleware, block_malicious_payload
from services.security.validation_chain import validate_and_sanitize
from security_integration import audit_sensitive_action
```

## Step 2: Add Middleware to Routes

### Simple Protection
```python
@bp.route('/api/endpoint', methods=['POST'])
@showwise_security_middleware
def my_endpoint():
    # Your existing code
    pass
```

### With Input Validation
```python
@bp.route('/api/endpoint', methods=['POST'])
@showwise_security_middleware
@block_malicious_payload
def my_endpoint():
    ip = get_client_ip()
    is_blocked, reason = check_ip_blocked(ip)
    
    if is_blocked:
        return jsonify({'error': 'Access denied'}), 403
    
    # Your endpoint code
    pass
```

### With Full Validation Chain
```python
@bp.route('/form/submit', methods=['POST'])
@showwise_security_middleware
@block_malicious_payload
@audit_sensitive_action('form_submission')
def submit_form():
    ip = get_client_ip()
    
    # Get and validate email
    email_raw = request.form.get('email', '')
    email, errors = validate_and_sanitize('email', email_raw)
    if errors:
        log_security_event('validation_failed', ip, severity='medium')
        return jsonify({'error': 'Invalid email'}), 400
    
    # Get and validate message
    message_raw = request.form.get('message', '')
    message, errors = validate_and_sanitize('message', message_raw)
    if errors:
        log_security_event('validation_failed', ip, severity='medium')
        return jsonify({'error': 'Invalid message'}), 400
    
    # Now use email and message safely
    # ...
    
    return jsonify({'success': True}), 200
```

## Step 3: Add Security Logging

```python
from services.security.security_utils import log_security_event, ThreatLevel

# Log successful operations
log_security_event(
    'user_action_completed',
    ip_address=get_client_ip(),
    user_id=current_user.id,
    username=current_user.username,
    severity=ThreatLevel.LOW.value,
    description='User deleted account'
)

# Log suspicious activity
log_security_event(
    'suspicious_activity',
    ip_address=ip,
    severity=ThreatLevel.MEDIUM.value,
    description='Multiple failed attempts detected'
)
```

## Step 4: Update Templates for Turnstile (home page)

```html
<!-- Add to contact form template -->

<form method="POST" action="/contact/submit">
    <input type="email" name="email" required>
    <textarea name="message" required></textarea>
    
    <!-- Cloudflare Turnstile -->
    <div class="cf-turnstile" 
         data-sitekey="{{ config.CLOUDFLARE_TURNSTILE_SITE_KEY }}"
         data-theme="light"></div>
    
    <button type="submit">Submit</button>
</form>

<!-- Add before closing body tag -->
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>

<!-- Optional: Handle Turnstile errors -->
<script>
window.onloadTurnstileCallback = function () {
    console.log('Turnstile loaded');
};
</script>
```

## Step 5: Environment Variables

Add to your `.env`:

```
# Security Backend
SECURITY_BACKEND_URL=http://localhost:5001
API_INTEGRATION_KEY=your-32-char-key
API_INTEGRATION_SECRET=your-32-char-secret
APP_INSTANCE_NAME=main

# Cloudflare Turnstile (for home page forms)
CLOUDFLARE_TURNSTILE_SITE_KEY=1x1...
CLOUDFLARE_TURNSTILE_SECRET=1x1...

# Security Settings
CHECK_CLOUDFLARE_THREAT=True
BLOCK_SCANNERS=True
SANITIZE_INPUT=True
```

## Step 6: Initialize Security in app.py

```python
from services.security import init_security

app = Flask(__name__)
app.config.from_object(get_config())

# Initialize security features
init_security(app)

# Rest of your app setup...
```

## Step 7: Common Integration Patterns

### Login Endpoint
```python
@bp.route('/login', methods=['POST'])
@showwise_security_middleware
@block_malicious_payload
def login():
    ip = get_client_ip()
    
    # Check if IP is blocked
    is_blocked, reason = check_ip_blocked(ip)
    if is_blocked:
        log_security_event('login_blocked_ip', ip, severity='high')
        return jsonify({'error': 'Access denied'}), 403
    
    username = request.json.get('username')
    password = request.json.get('password')
    
    # Your login logic with password checking and 2FA
    
    log_security_event(
        'login_successful',
        ip,
        user_id=user.id,
        username=username,
        severity='low'
    )
    return jsonify({'success': True}), 200
```

### Contact Form
```python
@bp.route('/contact', methods=['POST'])
@limiter.limit("5 per minute")
@showwise_security_middleware
@block_malicious_payload
def contact_form():
    ip = get_client_ip()
    
    # Verify Turnstile
    from services.security.cloudflare_integration import CloudflareIntegration
    token = request.form.get('cf-turnstile-response')
    is_human, msg = CloudflareIntegration.verify_turnstile_token(token)
    if not is_human:
        return jsonify({'error': 'CAPTCHA failed'}), 400
    
    # Validate inputs
    name, errors = validate_and_sanitize('username', request.form.get('name'))
    if errors:
        return jsonify({'error': 'Invalid name'}), 400
    
    email, errors = validate_and_sanitize('email', request.form.get('email'))
    if errors:
        return jsonify({'error': 'Invalid email'}), 400
    
    message, errors = validate_and_sanitize('message', request.form.get('message'))
    if errors:
        return jsonify({'error': 'Invalid message'}), 400
    
    # Send email with sanitized data
    # ...
    
    log_security_event('contact_submitted', ip, severity='low')
    return jsonify({'success': True}), 200
```

### Admin Endpoint
```python
@bp.route('/admin/users', methods=['GET'])
@login_required
@admin_required
@showwise_security_middleware
def admin_users():
    ip = get_client_ip()
    
    # Log admin access
    log_security_event(
        'admin_access',
        ip,
        user_id=current_user.id,
        username=current_user.username,
        severity='medium',
        description='Accessed admin panel - users'
    )
    
    # Return user list
    
    return jsonify({'users': [...]}), 200
```

## Step 8: Testing Your Integration

```python
# Test script
import requests
import json

BASE_URL = 'http://localhost:5000'

# Test 1: Check IP blocklist
response = requests.get(
    f'{BASE_URL}/api/ip/status/192.168.1.1',
    headers={'X-API-Key': 'your-key'}
)
print("IP Status:", response.json())

# Test 2: Scanner detection
response = requests.get(
    f'{BASE_URL}/api/test',
    headers={'User-Agent': 'BurpSuite/2023'}
)
print("Scanner Test:", response.status_code)  # Should be 403

# Test 3: SQLi detection
response = requests.post(
    f'{BASE_URL}/api/test',
    json={'input': "test' OR '1'='1"}
)
print("SQLi Test:", response.status_code)  # Should be 400

# Test 4: Valid request
response = requests.post(
    f'{BASE_URL}/api/test',
    json={'input': 'normal input'}
)
print("Valid Request:", response.status_code)  # Should be 200
```

## Advanced: Custom Validators

Create your own validation rules:

```python
from services.security.validation_chain import ValidationChain

# Custom username validator
custom_validator = ValidationChain()
custom_validator.add_validator(lambda x: len(x) >= 5 or 'Username too short')
custom_validator.add_validator(lambda x: not x.startswith('admin') or 'Reserved username')
custom_validator.add_validator(lambda x: not any(c in x for c in '!@#$%') or 'Invalid characters')
custom_validator.add_sanitizer(lambda x: x.lower().strip())

# Use it
is_valid, errors = custom_validator.validate(username_input)
if is_valid:
    username = custom_validator.sanitize(username_input)
```

## Troubleshooting

### Issue: "Invalid signature" when calling backend
**Solution**: Ensure API_INTEGRATION_SECRET is identical across all services

### Issue: Turnstile always fails
**Solution**: Check CLOUDFLARE_TURNSTILE_SITE_KEY and CLOUDFLARE_TURNSTILE_SECRET are correct

### Issue: Legitimate users getting blocked
**Solution**: Check `/api/admin/blocked-list` and `/api/appeals/submit` for appeals

### Issue: Rate limiting too strict
**Solution**: Adjust limits in environment or per-route
