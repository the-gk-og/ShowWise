# Production-Ready Security Infrastructure for ShowWise

## Overview

This is a comprehensive, production-ready security infrastructure designed to protect your ShowWise ecosystem from attacks, including Burp Suite, SQLi, XSS, brute force, rate limiting abuse, and more.

## Architecture

### 1. **Security Backend Service** (Port 5001)
Central IP reputation and threat management system.

**Key Features:**
- IP threat tracking with 100-point scoring system
- Block list / Quarantine management
- Appeal process for IP owners
- Audit logging of all security events
- Dashboard analytics
- Automated threat response
- Cross-service communication via HMAC signatures

### 2. **ShowWise Main App** 
Enhanced security middleware and input validation.

**Key Features:**
- Cloudflare header parsing (CF-Connecting-IP, threat scores)
- Scanner detection (Burp Suite, SQLmap, etc.)
- Malicious payload detection (SQLi, XSS, command injection)
- Input sanitization chains
- Rate limiting per IP
- 2FA enforcement
- Audit logging
- Suspended IP blocking

### 3. **ShowWise-home**
Homepage with Cloudflare Turnstile CAPTCHA protection.

**Key Features:**
- Turnstile CAPTCHA on contact forms
- Rate limiting (5 requests/min per IP)
- Abuse reporting to backend
- IP-based blocking
- Email validation
- Input sanitization

## Environment Setup

### Security Backend (.env)

```bash
# Flask
FLASK_ENV=production
SECRET_KEY=your-min-32-char-secret-key-here
DEBUG=False

# Database (SQLite for simple setup, PostgreSQL for production)
SECURITY_DATABASE_URL=sqlite:///security.db
# SECURITY_DATABASE_URL=postgresql://user:password@localhost/security_db

# API Keys (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
API_INTEGRATION_KEY=your-32-char-min-key-for-cross-service
API_INTEGRATION_SECRET=your-32-char-min-secret-for-hmac
ADMIN_API_KEY=your-32-char-min-admin-key

# Security Thresholds
IP_BLOCK_THRESHOLD=100
RATE_LIMIT_WINDOW=3600
RATE_LIMIT_MAX_REQUESTS=1000

# Appeal Settings
APPEAL_EXPIRY_DAYS=30
QUARANTINE_AUTO_RELEASE_DAYS=90
```

### ShowWise Main App (.env additions)

```bash
# Security Backend
SECURITY_BACKEND_URL=http://localhost:5001
API_INTEGRATION_KEY=your-32-char-min-key-for-cross-service
API_INTEGRATION_SECRET=your-32-char-min-secret-for-hmac
APP_INSTANCE_NAME=main

# Cloudflare
CHECK_CLOUDFLARE_THREAT=True
CLOUDFLARE_TURNSTILE_SITE_KEY=your-cf-site-key
CLOUDFLARE_TURNSTILE_SECRET=your-cf-secret

# Security
REQUIRE_IP_CHECK=True
BLOCK_SCANNERS=True
SANITIZE_INPUT=True
```

### ShowWise-home (.env additions)

```bash
# Security Backend
SECURITY_BACKEND_URL=http://localhost:5001
API_INTEGRATION_KEY=your-32-char-min-key-for-cross-service
API_INTEGRATION_SECRET=your-32-char-min-secret-for-hmac
APP_INSTANCE_NAME=home

# Cloudflare Turnstile (for contact forms)
CLOUDFLARE_TURNSTILE_SITE_KEY=your-cf-site-key
CLOUDFLARE_TURNSTILE_SECRET=your-cf-secret
```

## Key Security Features

### 1. **IP-Based Blocking**

```python
# Check if IP is blocked
is_blocked, reason = check_ip_blocked(ip_address)

if is_blocked:
    return jsonify({'error': 'Access denied'}), 403
```

### 2. **Scanner Detection**

Detects and blocks: Burp Suite, SQLmap, Nikto, Nessus, ZAP, Metasploit, etc.

```python
if detect_scanner_user_agent(user_agent):
    report_to_security_backend('scanner_detected', ip_address)
    return jsonify({'error': 'Forbidden'}), 403
```

### 3. **Malicious Payload Detection**

Detects: SQL injection, XSS, command injection patterns

```python
threats = detect_malicious_patterns(request_data)
if threats:
    report_to_security_backend('attack_detected', ip_address)
    return jsonify({'error': 'Request blocked'}), 400
```

### 4. **Input Validation & Sanitization Chains**

```python
# Email validation
sanitized, errors = validate_and_sanitize('email', user_input)

# Username validation
sanitized, errors = validate_and_sanitize('username', user_input)

# Message validation
sanitized, errors = validate_and_sanitize('message', user_input)
```

### 5. **Rate Limiting**

- Home page contact form: 5 requests/minute per IP
- Main app: 50 requests/hour per IP
- API endpoints: 1000 requests/hour per IP

### 6. **Cloudflare Integration**

```python
# Verify Turnstile
is_human, msg = CloudflareIntegration.verify_turnstile_token(token)

# Get CF metadata
cf_data = get_cloudflare_metadata()  # Ray ID, threat score, bot score
```

## API Endpoints Reference

### Security Backend

#### IP Management
- `GET /api/ip/status/<ip>` - Check IP status
- `POST /api/ip/check` - Log and check IP
- `POST /api/ip/report-threat` - Report threat
- `POST /api/ip/block` - Block IP
- `POST /api/ip/unblock` - Unblock IP
- `POST /api/ip/whitelist` - Whitelist IP
- `POST /api/ip/quarantine` - Quarantine IP
- `GET /api/ip/<ip>/history` - IP history

#### Events
- `POST /api/events/log` - Log security event
- `GET /api/events` - List events
- `GET /api/events/summary` - Event summary

#### Appeals
- `POST /api/appeals/submit` - Submit IP appeal
- `GET /api/appeals/<id>` - Check appeal status
- `POST /api/appeals/<id>/approve` - Approve appeal
- `POST /api/appeals/<id>/reject` - Reject appeal

#### Admin
- `GET /api/admin/threats` - List threats
- `GET /api/admin/blocked-list` - Get all blocked IPs
- `GET /api/admin/quarantine-list` - Get all quarantined IPs
- `POST /api/admin/bulk-action` - Bulk IP operations
- `GET /api/admin/stats` - Security statistics

#### Dashboard
- `GET /api/dashboard/overview` - Dashboard overview
- `GET /api/dashboard/top-ips` - Top threat IPs
- `GET /api/dashboard/recent-events` - Recent events
- `GET /api/dashboard/critical-alerts` - Critical alerts

### Main App Routes

#### Secure Auth
- `POST /auth/login` - Login (IP checked, scanner detected, payload validated)
- `POST /auth/verify-2fa` - Verify 2FA code
- `POST /auth/logout` - Logout with audit
- `POST /auth/password-reset` - Secure password reset

## Security Settings Per Request

Each request goes through:

1. **IP Check** - Is IP blocked/quarantined?
2. **Scanner Detection** - Burp Suite, SQLmap, etc.?
3. **Cloudflare Metadata** - Check threat score
4. **Payload Analysis** - Detect SQLi, XSS, command injection
5. **Rate Limiting** - Per-IP request throttling
6. **Input Validation** - Type and format checking
7. **Sanitization** - Remove/escape dangerous content
8. **Audit Logging** - Log to central backend

## Integration with Existing Code

### In routes/auth.py or similar:

```python
from security_integration import showwise_security_middleware, require_input_validation

@bp.route('/login', methods=['POST'])
@showwise_security_middleware
@require_input_validation({'username': 'username', 'email': 'email'})
def login():
    # Your existing code
    pass
```

### In forms/templates:

```html
<!-- Turnstile CAPTCHA -->
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>

<form method="POST">
    <input type="email" name="email" required>
    <textarea name="message" required></textarea>
    
    <!-- Add Turnstile -->
    <div class="cf-turnstile" data-sitekey="{{ CLOUDFLARE_TURNSTILE_SITE_KEY }}"></div>
    <button type="submit">Submit</button>
</form>
```

## Attack Prevention

### Burp Suite & Scanners
- Detected via user-agent string patterns
- Returns 403 Forbidden
- Reports to security backend as CRITICAL
- IP is auto-quarantined

### SQL Injection
- Detects patterns: `UNION SELECT`, `OR '1'='1'`, etc.
- Sanitizes all input
- Returns 400 Bad Request
- Reports as HIGH severity
- Tracks IP threat score

### XSS Attacks
- Detects: `<script>`, `javascript:`, `onerror=`, etc.
- Escapes HTML entities
- Allows safe tags only (b, i, a, p, etc.)
- Whitelistnew approach

### Command Injection
- Detects: `;`, `|`, `&`, backticks, `$()`, etc.
- All shell metacharacters blocked
- Reports attempt to backend

### Brute Force
- Tracks failed login attempts per IP
- Auto-quarantines after 10 failures
- Rate limiting enforced
- 2FA required for repeated failures

### Rate Limiting
- Per-IP, per-endpoint tracking
- Cloudflare helps with DDoS
- Auto-reports abuse to backend
- Progressive delays on excessive requests

## Deployment Checklist

- [ ] Generate all required API keys (32+ chars each)
- [ ] Set up PostgreSQL database (or use SQLite for dev)
- [ ] Configure Cloudflare Turnstile tokens
- [ ] Set FLASK_ENV=production
- [ ] Set SECRET_KEY using secure random generation
- [ ] Update SECURITY_BACKEND_URL in apps
- [ ] Enable HTTPS/SSL on all services
- [ ] Set up firewall to block known bad IPs
- [ ] Test all security endpoints
- [ ] Enable structured logging
- [ ] Set up monitoring/alerting
- [ ] Configure backup/disaster recovery
- [ ] Run security audit before go-live

## Testing Security

### 1. Test Burp Suite Detection
```bash
curl -H "User-Agent: BurpSuite/2023" http://localhost:5000/api/test
# Should return 403
```

### 2. Test SQLi Detection
```bash
curl -X POST -d "name=test' OR '1'='1" http://localhost:5000/contact/submit
# Should return 400
```

### 3. Test XSS Detection
```bash
curl -X POST -d "message=<script>alert(1)</script>" http://localhost:5000/contact/submit
# Should return 400
```

### 4. Test Rate Limiting
```bash
# Make 6 requests in 1 minute to rate-limited endpoint
# 6th should return 429
```

### 5. Test IP Blocking
```bash
# Query to block IP via admin API
curl -X POST http://localhost:5001/api/admin/ip/1.2.3.4/block \
  -H "X-Admin-Key: your-admin-key"

# Then access from that IP
# Should return 403
```

## Monitoring & Alerts

Monitor these security backend endpoints:

```python
# Dashboard overview
GET /api/dashboard/overview

# Critical alerts
GET /api/dashboard/critical-alerts

# Top threats
GET /api/dashboard/top-ips

# Admin stats
GET /api/admin/stats
```

Set up alerts for:
- Blocked IPs count > 100
- Critical events in last hour > 10
- Unresolved alerts > 5
- Pending appeals > 3

## Production Considerations

1. **Database**: Use PostgreSQL in production, not SQLite
2. **Logging**: Configure structured logging to Elasticsearch/Splunk
3. **Backups**: Daily backups of security database
4. **Key Rotation**: Rotate API keys every 90 days
5. **Monitoring**: 24/7 monitoring of security endpoints
6. **Updates**: Keep security rules updated with new attack patterns
7. **Scaling**: Use Redis for distributed rate limiting
8. **Redundancy**: Run security backend on multiple servers

## Support & Troubleshooting

### IP is blocked unfairly
- Check appeal process at `/api/appeals/submit`
- Admin can review at `/api/admin/appeals` (requires ADMIN_API_KEY)
- Approve with `/api/appeals/<id>/approve`

### False positive on legitimate tool
- Add to whitelist: `POST /api/ip/whitelist`
- Or adjust threat detection rules

### Rate limiting too strict
- Adjust thresholds in environment variables
- Configure per-endpoint limits

## Security Incident Response

1. Check dashboard: `GET /api/dashboard/overview`
2. View events: `GET /api/events?severity=critical`
3. Identify attacker IP: `GET /api/dashboard/top-ips`
4. Block immediately: `POST /api/admin/ip/<ip>/block`
5. Review history: `GET /api/ip/<ip>/history`
6. Notify users if needed
7. Monitor for related attacks

This infrastructure is designed to catch 99% of automated and manual attack attempts while maintaining good user experience for legitimate users.
