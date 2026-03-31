# 🐳 ShowWise Security Infrastructure - Docker Stack for TrueNAS

**Production-ready Docker Compose stack for TrueNAS deployment**

---

## 📋 Prerequisites

- ✅ TrueNAS (Scale or Core with Docker)
- ✅ SSH access to TrueNAS
- ✅ Git installed
- ✅ Docker and Docker Compose enabled
- ✅ 50GB+ free storage
- ✅ GitHub account

---

## 🚀 Quick Start (5 Minutes)

### Step 1: SSH into TrueNAS

```bash
ssh root@your-truenas-ip
```

Or use **System → Shell** in TrueNAS Web UI

### Step 2: One-Command Setup

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/your-username/Active-ShowWise/main/setup-truenas.sh)"
```

**That's it!** Services will be running at:
- 🔒 Security Backend: http://truenas-ip:5001
- 📱 ShowWise Main: http://truenas-ip:5000
- 🏠 ShowWise Home: http://truenas-ip:5002
- 🗄️ ShowWise Backend: http://truenas-ip:5003

---

## 📋 Manual Setup (If You Prefer)

### Step 1: Clone Repository

```bash
cd /root
git clone https://github.com/your-username/Active-ShowWise.git showwise-security
cd showwise-security
```

### Step 2: Generate Security Keys

```bash
python3 << 'EOF'
import secrets
keys = {
    'API_INTEGRATION_KEY': secrets.token_urlsafe(32),
    'API_INTEGRATION_SECRET': secrets.token_urlsafe(32),
    'ADMIN_API_KEY': secrets.token_urlsafe(32),
    'SECURITY_SECRET_KEY': secrets.token_urlsafe(32),
    'SHOWWISE_SECRET_KEY': secrets.token_urlsafe(32),
    'HOME_SECRET_KEY': secrets.token_urlsafe(32),
    'BACKEND_SECRET_KEY': secrets.token_urlsafe(32),
}
for k, v in keys.items():
    print(f"{k}={v}")
EOF
```

**Copy the output** - you'll need these values next.

### Step 3: Create .env File

```bash
cat > /root/showwise-security/.env << 'EOF'
# API Keys (PASTE FROM STEP 2)
API_INTEGRATION_KEY=<generated-key>
API_INTEGRATION_SECRET=<generated-key>
ADMIN_API_KEY=<generated-key>
SECURITY_SECRET_KEY=<generated-key>
SHOWWISE_SECRET_KEY=<generated-key>
HOME_SECRET_KEY=<generated-key>
BACKEND_SECRET_KEY=<generated-key>

# Database
POSTGRES_USER=security_user
POSTGRES_PASSWORD=securepassword123!
POSTGRES_DB=security_db

# Cloudflare Turnstile (Optional - get from https://dash.cloudflare.com/)
CLOUDFLARE_SITE_KEY=your-site-key
CLOUDFLARE_SECRET=your-secret-key
EOF

chmod 600 /root/showwise-security/.env
```

### Step 4: Deploy the Stack

```bash
cd /root/showwise-security

# Create data directories
mkdir -p data/postgres data/redis backups logs
chmod 777 data/* logs backups

# Build all Docker images
docker-compose -f docker-compose.truenas.yml build

# Start the complete stack
docker-compose -f docker-compose.truenas.yml up -d

# Verify all services are running
docker-compose -f docker-compose.truenas.yml ps
```

### Step 5: Verify Stack Status

```bash
# Check all container health
docker-compose -f docker-compose.truenas.yml ps

# Expected: All services show "healthy" or "Up"

# Test endpoints
curl http://localhost:5001/health   # Security Backend
curl http://localhost:5000/health   # ShowWise Main
curl http://localhost:5002/health   # ShowWise Home
curl http://localhost:5003/health   # ShowWise Backend
```

---

## 🏗️ Docker Stack Configuration

The `docker-compose.truenas.yml` file contains the complete stack with 6 services:

| Service | Port | Purpose |
|---------|------|---------|
| **security-db** | 5432 | PostgreSQL database |
| **redis** | 6379 | Cache & rate limiting |
| **security-backend** | 5001 | IP reputation & threat management |
| **showwise-main** | 5000 | Primary ShowWise application |
| **showwise-home** | 5002 | Public home page & forms |
| **showwise-backend** | 5003 | Original database backend |

---

## 🏗️ Step 7: Build and Deploy the Stack

```bash
cd /root/showwise-security

# Create data directories
mkdir -p data/postgres data/redis backups logs
chmod 777 data/* logs backups

# Build all Docker images (5-10 minutes)
docker-compose -f docker-compose.truenas.yml build

# Start the complete stack
docker-compose -f docker-compose.truenas.yml up -d

# Verify all services are running
docker-compose -f docker-compose.truenas.yml ps
```

---

## ✅ Step 8: Verify Stack Health

```bash
# View all running services
docker-compose -f docker-compose.truenas.yml ps

# Expected: All services show "(healthy)" or "(Up)"

# Test endpoints
curl http://localhost:5001/health   # Security Backend
curl http://localhost:5000/health   # ShowWise Main
curl http://localhost:5002/health   # ShowWise Home
curl http://localhost:5003/health   # ShowWise Backend
```

---

## 📊 Step 9: Monitor Stack

```bash
# View all logs
docker-compose -f docker-compose.truenas.yml logs -f

# View specific service
docker-compose -f docker-compose.truenas.yml logs -f security-backend

# View resource usage
docker stats

# View recent logs (last 50 lines)
docker-compose -f docker-compose.truenas.yml logs --tail=50
```

---

## 🔄 Step 10: Update and Maintain Stack

### Update from GitHub
```bash
cd /root/showwise-security
git pull origin main
docker-compose -f docker-compose.truenas.yml build --no-cache
docker-compose -f docker-compose.truenas.yml up -d
```

### Restart Stack
```bash
docker-compose -f docker-compose.truenas.yml restart
```

### Stop Stack
```bash
docker-compose -f docker-compose.truenas.yml stop
```

### View Stack Status

---

## 🔧 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose -f docker-compose.truenas.yml logs security-backend

# Restart a specific service
docker-compose -f docker-compose.truenas.yml restart security-backend

# Rebuild the image
docker-compose -f docker-compose.truenas.yml build --no-cache security-backend
```

### Port already in use
```bash
# Find what's using the port
lsof -i :5001

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.truenas.yml
# Change "5001:5000" to "5001:5000" -> "5011:5000"
```

### Database connection error
```bash
# Wait 30 seconds for database to be ready, then restart backend
docker-compose -f docker-compose.truenas.yml restart security-backend

# Check if database service is healthy
docker-compose -f docker-compose.truenas.yml ps security-db
```

### Out of disk space
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune
docker container prune
docker image prune
```

---

## 📂 Directory Structure on TrueNAS

After setup, your directory structure should look like:

```
/root/showwise-security/
├── ShowWise/
├── ShowWise-Backend/
├── ShowWise-home/
├── ShowWise-SecurityBackend/
├── docker-compose.truenas.yml
├── .env
├── data/
│   ├── postgres/          # PostgreSQL data
│   └── redis/             # Redis data
├── backups/               # Database backups
└── logs/                  # Application logs
```

---

## 🌐 Access Your Services

Once running, access these URLs from your network:

| Service | URL | Port |
|---------|-----|------|
| **Security Backend** | http://truenas-ip:5001 | 5001 |
| **ShowWise Main** | http://truenas-ip:5000 | 5000 |
| **ShowWise Home** | http://truenas-ip:5002 | 5002 |
| **ShowWise Backend** | http://truenas-ip:5003 | 5003 |
| **PostgreSQL** | localhost:5432 | 5432 |
| **Redis** | localhost:6379 | 6379 |

---

## 📱 Monitor from TrueNAS Web UI

Optional: Add Docker monitoring to TrueNAS

1. Go to **System → Update**
2. Check for Docker or Portainer updates
3. Install Portainer for visual container management

Or use command line:

```bash
# View real-time stats
docker stats

# View Docker events
docker events --filter type=container
```

---

## 🔐 Security Notes

### Before Production:

- [ ] Change all default passwords in `.env`
- [ ] Set strong database password
- [ ] Enable SSL/TLS with reverse proxy
- [ ] Set up firewall rules (allow only needed ports)
- [ ] Enable automatic backups
- [ ] Set up monitoring/alerting
- [ ] Review security logs regularly

### Firewall Rules Example:
```bash
# Allow only specific ports
ufw allow 5001/tcp   # Security Backend
ufw allow 5000/tcp   # ShowWise Main
ufw allow 5002/tcp   # ShowWise Home
ufw allow 5003/tcp   # ShowWise Backend
ufw enable
```

---

## 📞 Common Commands Reference

```bash
# Start stack
docker-compose -f docker-compose.truenas.yml up -d

# Stop stack
docker-compose -f docker-compose.truenas.yml stop

# View status
docker-compose -f docker-compose.truenas.yml ps

# View logs
docker-compose -f docker-compose.truenas.yml logs -f

# Rebuild images
docker-compose -f docker-compose.truenas.yml build --no-cache

# Execute command in container
docker-compose -f docker-compose.truenas.yml exec security-backend bash

# Update from GitHub
cd /root/showwise-security && git pull origin main

# Backup database
docker-compose -f docker-compose.truenas.yml exec security-db \
  pg_dump -U security_user -d security_db > backups/backup.sql
```

---

## ✅ Setup Complete!

Your ShowWise security infrastructure is now running on TrueNAS with:

✅ 4 separate Flask applications (in 4 Docker containers)
✅ PostgreSQL database on TrueNAS
✅ Redis caching
✅ All services auto-restarting on failure
✅ Health monitoring
✅ Persistent storage
✅ Automatic log rotation

**Next Steps:**
1. Update configuration in `.env` with your actual Cloudflare credentials
2. Access the dashboard at `http://truenas-ip:5001/api/dashboard/overview`
3. Set up monitoring and alerting
4. Configure SSL/TLS with reverse proxy
5. Plan regular backups

---

**Questions?** Check SECURITY_INFRASTRUCTURE.md for detailed API documentation.
