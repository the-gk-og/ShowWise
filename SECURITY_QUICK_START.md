# Quick Start - Security Infrastructure

## Prerequisites
- Python 3.9+
- Docker & Docker Compose
- PostgreSQL (or use Docker)
- Redis (or use Docker)

## Setup Steps

### 1. Generate Required Keys
```bash
python -c "import secrets; print('API_INTEGRATION_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('API_INTEGRATION_SECRET=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('ADMIN_API_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('SECURITY_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('SHOWWISE_SECRET_KEY=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('HOME_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

### 2. Copy `.env.security.example` to `.env`
```bash
cp .env.security.example .env
# Edit .env and add the generated keys and Cloudflare credentials
```

### 3. Start Services
```bash
docker-compose -f docker-compose.security.yml up -d
```

### 4. Initialize Databases
```bash
# Security Backend
docker-compose -f docker-compose.security.yml exec security-backend flask db upgrade

# ShowWise Main
docker-compose -f docker-compose.security.yml exec showwise-main flask db upgrade
```

### 5. Create Admin User
```bash
curl -X POST http://localhost:5001/api/admin/user/create \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@security.local",
    "password": "secure-password-here",
    "is_admin": true
  }'
```

---

## Testing Security Features

### Test 1: Check IP Status
```bash
curl -H "X-API-Key: your-api-integration-key" \
  http://localhost:5001/api/ip/status/192.168.1.1
```

### Test 2: Block an IP
```bash
curl -X POST http://localhost:5001/api/admin/ip/192.168.1.1/block \
  -H "X-Admin-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"reason": "test_block", "admin_email": "admin@test"}'
```

### Test 3: Report Threat
```bash
curl -X POST http://localhost:5001/api/ip/report-threat \
  -H "X-API-Key: your-api-integration-key" \
  -H "Content-Type: application/json" \
  -d '{
    "ip_address": "192.168.1.1",
    "threat_type": "sql_injection",
    "severity": "high",
    "description": "SQL injection attempt in login",
    "service": "main"
  }'
```

### Test 4: Contact Form (with Turnstile)
```bash
# First get a valid Turnstile token, then:
curl -X POST http://localhost:5002/contact/submit \
  -d "name=Test&email=test@example.com&message=Hello&cf-turnstile-response=valid-token"
```

### Test 5: Dashboard Overview
```bash
curl -H "X-API-Key: your-api-integration-key" \
  http://localhost:5001/api/dashboard/overview
```

---

## Monitoring

### View Security Logs
```bash
# Recent events
curl -H "X-API-Key: your-api-integration-key" \
  "http://localhost:5001/api/events?limit=50"

# Top threatened IPs
curl -H "X-API-Key: your-api-integration-key" \
  "http://localhost:5001/api/dashboard/top-ips?limit=10"

# Pending appeals
curl -H "X-API-Key: your-api-integration-key" \
  "http://localhost:5001/api/dashboard/pending-appeals"
```

---

## Production Deployment

### 1. Environment Setup
- Update all keys in `.env` with production values
- Set `FLASK_ENV=production`
- Use PostgreSQL with strong credentials
- Enable SSL/TLS for all services

### 2. Cloudflare Configuration
- Get Turnstile Site Key & Secret from Cloudflare dashboard
- Add routing rules to tunnel through Cloudflare
- Enable CF-IPCountry and CF-Threat-Score headers

### 3. Database Backups
```bash
# Backup security database
pg_dump -U security_user -h localhost security_db > backup.sql

# Automate with cron:
0 2 * * * pg_dump -U security_user -h localhost security_db | gzip > /backups/security_db_$(date +%Y%m%d).sql.gz
```

### 4. Monitoring & Alerting
```bash
# Set up alerts when:
- Blocked IPs > 50
- Critical events/hour > 5
- Appeals pending > 3
- Service down
```

### 5. Key Rotation (Every 90 days)
```bash
# Generate new keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in database and .env
# Restart services
```

---

## Common Issues

### 1. "Invalid signature" error
- Ensure API_INTEGRATION_SECRET matches across all services
- Check request data is not modified before sending

### 2. Rate limiting too strict
- Adjust RATE_LIMIT_WINDOW and RATE_LIMIT_MAX_REQUESTS in .env
- Default: 1000 requests/hour (about 17/min)

### 3. "IP is blocked" errors
- Check `/api/admin/blocked-list` to see all blocked IPs
- Unblock with `/api/admin/ip/<ip>/unblock`

### 4. Turnstile verification fails
- Verify Site Key matches in frontend and backend
- Check Cloudflare dashboard for token expiry
- Ensure origin domain matches Cloudflare config

---

## Support

For issues or questions:
1. Check logs: `docker-compose -f docker-compose.security.yml logs -f`
2. Review security events: `curl ... /api/events`
3. Check IP reputation: `curl ... /api/admin/threats`
