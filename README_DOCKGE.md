# ShowWise Dockge Deployment - Quick Start

## 📋 What You're Deploying

A complete ShowWise production stack with:
- **3 Separate PostgreSQL Databases** (Security, Organization, WebApp)
- **Redis Cache** for sessions and rate limiting
- **4 Flask Microservices** (Security Backend, Main App, Home App, Legacy Backend)
- **Dockge Compatible** - Use with Dockge container management system
- **Health Checks & Monitoring** built-in
- **Production-Ready** with proper logging and restart policies

---

## 🚀 Quick Start (5 Steps)

### Step 1: Prepare Environment (Automated)
```bash
chmod +x setup-dockge.sh
./setup-dockge.sh
```

This script will:
- ✅ Generate secure secrets automatically
- ✅ Prompt for database passwords
- ✅ Create .env file with all values
- ✅ Verify Docker is installed

### Step 2: Review Configuration
```bash
nano .env  # Edit any values if needed
```

**Must-Have Values:**
- Database passwords (already generated)
- Cloudflare Turnstile keys (get from: https://dash.cloudflare.com/)
- API integration keys
- Discord tokens (optional)

### Step 3: Start with Docker Compose
```bash
# One command to start everything
docker-compose -f docker-compose.dockge.yml --env-file .env up -d
```

### Step 4: Monitor Deployment
```bash
# Watch logs in real-time
docker-compose -f docker-compose.dockge.yml logs -f

# Or just check service status
docker-compose -f docker-compose.dockge.yml ps
```

### Step 5: Test Services
```bash
# MainApp should respond with 200
curl http://localhost:5000/health

# View all running containers
docker ps | grep showwise
```

---

## 📊 Database Architecture

```
┌─────────────────────────────────────────┐
│        ShowWise Dockge Stack            │
├─────────────────────────────────────────┤
│                                         │
│  ┌─ Security Backend                   │
│  │  └─→ security-db (PostgreSQL:5432)  │
│  │                                      │
│  ├─ ShowWise Main App                  │
│  │  └─→ webapp-db (PostgreSQL:5434)    │
│  │                                      │
│  ├─ ShowWise Home                      │
│  │  └─→ redis (Redis:6379)             │
│  │                                      │
│  └─ ShowWise Backend                   │
│     └─→ org-db (PostgreSQL:5433)       │
│                                         │
│  ✓ All services connected via network  │
│  ✓ Health checks every 30 seconds      │
│  ✓ Auto-restart on failure             │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🔌 Service Endpoints

| Service | Port | Purpose |
|---------|------|---------|
| ShowWise Main | `5000` | Primary application |
| Security Backend | `5001` | IP reputation & threat detection |
| ShowWise Home | `5002` | Public landing page |
| ShowWise Backend | `5003` | Legacy/original backend |
| Security DB | `5432` | Security data storage |
| Organization DB | `5433` | Organization/crew/equipment data |
| WebApp DB | `5434` | Users, events, bookings |
| Redis | `6379` | Cache & sessions (internal) |

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `docker-compose.dockge.yml` | Main docker compose configuration |
| `.env.example` | Template environment variables |
| `.env` | Your actual config (created by setup script) |
| `setup-dockge.sh` | Automated setup wizard |
| `DOCKGE_DEPLOYMENT_GUIDE.md` | Comprehensive deployment guide |
| `README_DOCKGE.md` | This file |

---

## ⚙️ Environment File Structure

```bash
# Database passwords (3 separate instances)
SECURITY_DB_PASSWORD=...
ORG_DB_PASSWORD=...
WEBAPP_DB_PASSWORD=...

# Secret keys (8 for each service/integration)
SECURITY_BACKEND_SECRET_KEY=...
SHOWWISE_MAIN_SECRET_KEY=...
SHOWWISE_HOME_SECRET_KEY=...
SHOWWISE_BACKEND_SECRET_KEY=...

# API credentials
API_INTEGRATION_KEY=...
API_INTEGRATION_SECRET=...
ADMIN_API_KEY=...

# Cloudflare (required for production)
CLOUDFLARE_TURNSTILE_SITE_KEY=...
CLOUDFLARE_TURNSTILE_SECRET_KEY=...

# Discord (optional)
DISCORD_BOT_TOKEN=...
DISCORD_GUILD_ID=...
```

---

## 🔍 Monitoring & Troubleshooting

### Check Service Health
```bash
# All containers and their status
docker-compose -f docker-compose.dockge.yml ps

# Detailed health info
docker inspect showwise-main --format='{{json .State.Health}}' | jq
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.dockge.yml logs

# Specific service
docker-compose -f docker-compose.dockge.yml logs showwise-main

# Last 50 lines with follow
docker-compose -f docker-compose.dockge.yml logs -f --tail 50 showwise-main
```

### Restart a Service
```bash
docker-compose -f docker-compose.dockge.yml restart showwise-main
```

### Test Database Connections
```bash
# Security DB
docker-compose -f docker-compose.dockge.yml exec security-db pg_isready -U security_user

# Organization DB
docker-compose -f docker-compose.dockge.yml exec organization-db pg_isready -U org_user

# WebApp DB
docker-compose -f docker-compose.dockge.yml exec webapp-db pg_isready -U webapp_user
```

### Test Redis
```bash
docker-compose -f docker-compose.dockge.yml exec redis redis-cli ping
# Should return: PONG
```

---

## 🐳 Using with Dockge UI

If using the Dockge web interface:

1. **Access Dockge**: `http://your-server:5001`
2. **New Stack** → Paste `docker-compose.dockge.yml`
3. **Environment** → Load `.env` file or paste variables
4. **Deploy** → Monitor in real-time
5. **Logs** → View all service logs in UI

---

## 📝 Common Tasks

### Backup Databases
```bash
# All three databases - one command
for db in security-db organization-db webapp-db; do
  docker-compose -f docker-compose.dockge.yml exec -T $db \
    pg_dump -U $(docker-compose -f docker-compose.dockge.yml config | grep -i user) backup_db | \
    gzip > "backup_${db}_$(date +%Y%m%d).sql.gz"
done
```

### Update a Service
```bash
# Rebuild and restart one service
docker-compose -f docker-compose.dockge.yml up -d --build showwise-main
```

### Stop All Services
```bash
docker-compose -f docker-compose.dockge.yml stop
```

### Remove Everything (WARNING: Deletes Data!)
```bash
docker-compose -f docker-compose.dockge.yml down -v
```

---

## 🔐 Security Checklist

- [ ] All database passwords changed from defaults
- [ ] API keys generated using `openssl rand -hex 32`
- [ ] Cloudflare Turnstile keys configured
- [ ] `.env` file NOT committed to git (check `.gitignore`)
- [ ] Firewall rules restrict external DB access to port 5432-5434
- [ ] Use reverse proxy (Nginx/Traefik) for TLS/SSL
- [ ] Enable backups before production use
- [ ] Monitor logs for security warnings

---

## 🆘 Troubleshooting

**Services won't start:**
```bash
docker-compose -f docker-compose.dockge.yml up --no-daemon  # See full errors
```

**Port already in use:**
```bash
# Find what's using port 5000
lsof -i :5000
# Kill if safe, or adjust ports in .env
```

**Databases not connecting:**
```bash
# Check if DB containers are running
docker ps | grep db

# View database logs
docker-compose -f docker-compose.dockge.yml logs security-db
```

**Out of disk space:**
```bash
# Clean up old Docker data
docker system prune -a
```

---

## 📚 More Information

- **Full Guide**: See [DOCKGE_DEPLOYMENT_GUIDE.md](DOCKGE_DEPLOYMENT_GUIDE.md)
- **GitHub Repo**: https://github.com/the-gk-og/ShowWise.git
- **Documentation**: Check `ShowWise/README/ShowWise_documentation.md`
- **Docker Docs**: https://docs.docker.com/
- **Dockge Docs**: https://dockge.kuma.pet/

---

## 🎯 Next Steps After Deployment

1. ✅ Verify all services are healthy
2. ✅ Run database migrations (if needed)
3. ✅ Test all endpoints responding
4. ✅ Configure reverse proxy/SSL
5. ✅ Set up automated backups
6. ✅ Monitor logs and alerts
7. ✅ Create admin users
8. ✅ Test core workflows (signup, login, events, etc.)

---

## 📞 Support

If you encounter issues:
1. Check service logs: `docker-compose -f docker-compose.dockge.yml logs -f`
2. Verify environment variables: `cat .env | grep -v "^#"`
3. Test connectivity between services
4. Check available disk space: `df -h`
5. Review Docker/Docker Compose versions

---

**Ready to deploy?** Run: `./setup-dockge.sh` then `docker-compose -f docker-compose.dockge.yml up -d`

**Last Updated**: March 31, 2026  
**Version**: 1.0
