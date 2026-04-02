# ShowWise Dockge Deployment Guide

## Overview
This guide provides instructions for deploying ShowWise and all its services using **Dockge**, a lightweight Docker container management system.

### Key Features of This Stack:
- **3 Separate PostgreSQL Databases** for isolation:
  - `security-db` (port 5432) - Security Backend data
  - `organization-db` (port 5433) - Organization/Backend data  
  - `webapp-db` (port 5434) - Main webapp data
- **Redis Cache** for sessions, rate limiting, and caching
- **4 Flask Services** with health checks and monitoring
- **Separate Environment Configuration** (.env file)
- **Dockge-Compatible** docker-compose format

---

## Pre-Deployment Steps

### 1. Clone the Repository
```bash
git clone https://github.com/the-gk-og/ShowWise.git
cd ShowWise
```

### 2. Install Dockge (on your Docker host)
```bash
# Using Docker Compose
docker run -d \
  --name dockge \
  -p 5001:5001 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ./dockge:/app/data \
  lscr.io/linuxserver/dockge:latest

# Or install locally via npm
npm install -g dockge
```

### 3. Prepare Environment File
```bash
# Copy the example environment file
cp .env.example .env

# Edit with your values
nano .env  # or your preferred editor
```

#### Critical Environment Variables to Update:
```bash
# Database Passwords (REQUIRED)
SECURITY_DB_PASSWORD=your_strong_password_here
ORG_DB_PASSWORD=your_strong_password_here
WEBAPP_DB_PASSWORD=your_strong_password_here

# Secret Keys (generate with: openssl rand -hex 32)
SECURITY_BACKEND_SECRET_KEY=<generate_new>
SHOWWISE_MAIN_SECRET_KEY=<generate_new>
SHOWWISE_HOME_SECRET_KEY=<generate_new>
SHOWWISE_BACKEND_SECRET_KEY=<generate_new>

# API Keys
API_INTEGRATION_KEY=<your_key>
API_INTEGRATION_SECRET=<your_secret>
ADMIN_API_KEY=<your_key>

# Cloudflare (required for production)
CLOUDFLARE_TURNSTILE_SITE_KEY=<your_site_key>
CLOUDFLARE_TURNSTILE_SECRET_KEY=<your_secret_key>

# Discord (optional)
DISCORD_BOT_TOKEN=<your_token>
DISCORD_GUILD_ID=<your_guild_id>
```

### 4. Generate Secure Secrets
```bash
# Generate 8 strong secrets (32 hex characters each)
for i in {1..8}; do
  echo "Secret $i: $(openssl rand -hex 32)"
done
```

---

## Deployment with Dockge

### Method 1: Using Dockge Web UI

1. **Access Dockge Dashboard**
   - Open your browser to `http://localhost:5001` (or your server IP)
   - Login with default credentials

2. **Create New Stack**
   - Click "New Stack"
   - Name: `showwise-production`
   - Paste contents of `docker-compose.dockge.yml`

3. **Add Environment Variables**
   - In the stack editor, go to "Environment" tab
   - Load from `.env` file or paste variables

4. **Deploy**
   - Click "Deploy"
   - Monitor logs in real-time

### Method 2: Using Docker Compose CLI (via Dockge CLI)

```bash
# Navigate to project directory
cd /path/to/ShowWise

# Create the stack
docker-compose -f docker-compose.dockge.yml --env-file .env up -d

# Monitor logs
docker-compose -f docker-compose.dockge.yml logs -f

# View only security backend logs
docker-compose -f docker-compose.dockge.yml logs -f security-backend

# View only main app logs
docker-compose -f docker-compose.dockge.yml logs -f showwise-main
```

---

## Service Endpoints After Deployment

| Service | Port | Internal URL | External URL |
|---------|------|--------------|--------------|
| Security Backend | 5001 | http://security-backend:5000 | http://localhost:5001 |
| ShowWise Main | 5000 | http://showwise-main:5000 | http://localhost:5000 |
| ShowWise Home | 5002 | http://showwise-home:5000 | http://localhost:5002 |
| ShowWise Backend | 5003 | http://showwise-backend:5000 | http://localhost:5003 |
| Redis | 6379 | redis://redis:6379 | N/A (internal only) |
| Security DB | 5432 | postgresql://security-db:5432 | localhost:5432 |
| Organization DB | 5433 | postgresql://organization-db:5432 | localhost:5433 |
| WebApp DB | 5434 | postgresql://webapp-db:5432 | localhost:5434 |

---

## Database Schema Migration

**Important**: After the first deployment, you may need to run database migrations.

```bash
# Run migrations in the showwise-main container
docker-compose -f docker-compose.dockge.yml exec showwise-main flask db upgrade

# Or for the backend
docker-compose -f docker-compose.dockge.yml exec showwise-backend flask db upgrade
```

Alternatively, if migrations are auto-run on startup, check container logs:
```bash
docker-compose -f docker-compose.dockge.yml logs showwise-main | grep -i migrate
```

---

## Database Backups

### Automated Backups
Create a backup script:

```bash
#!/bin/bash
# backup-showwise-dbs.sh

BACKUP_DIR="/backups/showwise"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Security DB
docker-compose -f docker-compose.dockge.yml exec -T security-db \
  pg_dump -U security_user security_db | \
  gzip > "$BACKUP_DIR/security_db_${BACKUP_DATE}.sql.gz"

# Backup Organization DB
docker-compose -f docker-compose.dockge.yml exec -T organization-db \
  pg_dump -U org_user organization_db | \
  gzip > "$BACKUP_DIR/organization_db_${BACKUP_DATE}.sql.gz"

# Backup WebApp DB
docker-compose -f docker-compose.dockge.yml exec -T webapp-db \
  pg_dump -U webapp_user showwise_db | \
  gzip > "$BACKUP_DIR/webapp_db_${BACKUP_DATE}.sql.gz"

echo "Backups completed: $(ls -lh $BACKUP_DIR | tail -3)"
```

Save this as `backup-showwise-dbs.sh` and add to crontab for automated backups:
```bash
chmod +x backup-showwise-dbs.sh
# Backup daily at 2 AM
crontab -e
# Add: 0 2 * * * /path/to/backup-showwise-dbs.sh
```

---

## Health Checks

All services have health checks configured. Monitor status:

```bash
# View all container health status
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check specific service health
docker-compose -f docker-compose.dockge.yml ps security-backend

# View health check logs
docker inspect showwise-main --format='{{json .State.Health}}' | jq
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find what's using port 5000
lsof -i :5000

# Kill process (if safe)
kill -9 <PID>

# Or use different port in .env
sed -i 's/SHOWWISE_MAIN_PORT=5000/SHOWWISE_MAIN_PORT=5010/g' .env
```

### Database Connection Issues
```bash
# Test database connections
docker-compose -f docker-compose.dockge.yml exec security-db \
  pg_isready -U security_user

# Check database logs
docker-compose -f docker-compose.dockge.yml logs security-db | tail -50
```

### Service Won't Start
```bash
# View full error logs
docker-compose -f docker-compose.dockge.yml logs --tail 100 showwise-main

# Rebuild containers if code changed
docker-compose -f docker-compose.dockge.yml up -d --build

# Remove volumes and restart fresh (CAUTION: deletes data)
docker-compose -f docker-compose.dockge.yml down -v
docker-compose -f docker-compose.dockge.yml up -d
```

### Redis Connection Issues
```bash
# Test Redis connectivity
docker-compose -f docker-compose.dockge.yml exec redis redis-cli ping

# View Redis logs
docker-compose -f docker-compose.dockge.yml logs redis
```

---

## Production Considerations

### 1. Reverse Proxy (Nginx/Traefik)
```nginx
# Example Nginx config
upstream showwise_main {
    server showwise-main:5000;
}

server {
    listen 80;
    server_name showwise.example.com;
    
    location / {
        proxy_pass http://showwise_main;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. SSL/TLS with Let's Encrypt
```bash
# Use docker-compose with Traefik for automatic SSL
# Or use Certbot with your reverse proxy
```

### 3. Database Persistence
- Volumes are configured in docker-compose.dockge.yml
- Ensure proper backup strategy implemented
- Monitor disk space regularly

### 4. Monitoring & Logging
- All services output JSON logs with docker
- Use ELK Stack, Loki, or Grafana for centralized logging
- Configure alerting for service failures

### 5. Security Hardening
```bash
# Update .env with strong passwords (already noted above)
# Enable firewall rules
# Use Docker secrets for sensitive data (advanced)
# Enable Docker content trust
# Regularly update base images
```

---

## Common Operations

### View Running Containers
```bash
docker-compose -f docker-compose.dockge.yml ps
```

### View All Logs
```bash
docker-compose -f docker-compose.dockge.yml logs -f
```

### Restart a Service
```bash
docker-compose -f docker-compose.dockge.yml restart showwise-main
```

### Rebuild a Service
```bash
docker-compose -f docker-compose.dockge.yml up -d --build showwise-main
```

### Stop All Services
```bash
docker-compose -f docker-compose.dockge.yml stop
```

### Remove All (INCLUDING DATA)
```bash
docker-compose -f docker-compose.dockge.yml down -v
```

---

## Support & Updates

For issues or updates:
- GitHub: https://github.com/the-gk-og/ShowWise.git
- Check Docker logs for specific errors
- Review source code in respective directories
- Check ShowWise documentation in `/ShowWise/README/`

---

## Quick Start Checklist

- [ ] Clone repository
- [ ] Copy `.env.example` to `.env`
- [ ] Generate and update all secrets in `.env`
- [ ] Install/access Dockge
- [ ] Upload `docker-compose.dockge.yml` to Dockge
- [ ] Load environment variables from `.env`
- [ ] Deploy stack
- [ ] Monitor logs for errors
- [ ] Verify all services are healthy (green status)
- [ ] Test service endpoints
- [ ] Run database migrations if needed
- [ ] Set up backups

---

**Last Updated**: March 31, 2026
**Version**: 1.0
