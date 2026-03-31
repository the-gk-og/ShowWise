# 🚀 TrueNAS Setup - Quick Reference

## One-Command Setup (Automated)

```bash
# SSH into TrueNAS first
ssh root@your-truenas-ip

# Run the automated setup script
bash -c "$(curl -fsSL https://raw.githubusercontent.com/your-username/Active-ShowWise/main/setup-truenas.sh)"
```

---

## Manual Setup (Quick Version)

```bash
# 1. Create directory and enter it
mkdir -p /root/showwise-security/data/postgres /root/showwise-security/data/redis /root/showwise-security/{backups,logs}
cd /root/showwise-security

# 2. Clone repository
git clone https://github.com/your-username/Active-ShowWise.git .

# 3. Generate keys
python3 -c "import secrets; [print(f'{k}={secrets.token_urlsafe(32)}') for k in ['API_KEY','API_SECRET','ADMIN_KEY','SECURITY_SECRET','SHOWWISE_SECRET','HOME_SECRET','BACKEND_SECRET']]"

# 4. Copy .env template and edit
cp .env.security.example .env
nano .env  # Edit with your keys and Cloudflare credentials

# 5. Create TrueNAS-specific docker-compose
# (See TRUENAS_SETUP_GUIDE.md Step 6 for full file)

# 6. Build and start
docker-compose -f docker-compose.truenas.yml build
docker-compose -f docker-compose.truenas.yml up -d

# 7. Verify
docker-compose -f docker-compose.truenas.yml ps
```

---

## Access Services

| Service | URL |
|---------|-----|
| Security Backend | http://truenas-ip:5001 |
| ShowWise Main | http://truenas-ip:5000 |
| ShowWise Home | http://truenas-ip:5002 |
| ShowWise Backend | http://truenas-ip:5003 |

---

## Essential Commands

### Monitor
```bash
docker-compose -f docker-compose.truenas.yml ps          # Status
docker-compose -f docker-compose.truenas.yml logs -f     # Live logs
docker stats                                              # Resource usage
```

### Control
```bash
docker-compose -f docker-compose.truenas.yml up -d       # Start
docker-compose -f docker-compose.truenas.yml stop        # Stop
docker-compose -f docker-compose.truenas.yml restart     # Restart
docker-compose -f docker-compose.truenas.yml down        # Remove (keep data)
```

### Maintenance
```bash
# Update from GitHub
cd /root/showwise-security && git pull && docker-compose -f docker-compose.truenas.yml build && docker-compose -f docker-compose.truenas.yml up -d

# Backup database
docker-compose -f docker-compose.truenas.yml exec security-db \
  pg_dump -U security_user -d security_db > backups/backup-$(date +%Y%m%d-%H%M%S).sql

# View database
docker-compose -f docker-compose.truenas.yml exec security-db \
  psql -U security_user -d security_db

# Shell into container
docker-compose -f docker-compose.truenas.yml exec security-backend bash
```

---

## Troubleshooting

### Services won't start
```bash
# Check what's wrong
docker-compose -f docker-compose.truenas.yml logs

# Rebuild and restart
docker-compose -f docker-compose.truenas.yml build --no-cache
docker-compose -f docker-compose.truenas.yml up -d
```

### Port conflicts
```bash
# Find process using port
lsof -i :5001

# Change port in docker-compose.truenas.yml or docker-compose.security.yml
# Example: "5001:5000" → "5011:5000"
```

### Disk full
```bash
# Clean Docker
docker system prune -a

# Check disk
df -h
```

### Database won't connect
```bash
# Wait 30 seconds for DB to start
sleep 30

# Restart backend services
docker-compose -f docker-compose.truenas.yml restart security-backend showwise-main showwise-home showwise-backend
```

---

## Security Checklist

- [ ] Generated strong API keys
- [ ] Set Cloudflare Turnstile credentials
- [ ] Changed default database password in .env
- [ ] Restricted port access via firewall
- [ ] Set up automated backups
- [ ] Enabled HTTPS with reverse proxy
- [ ] Reviewed container logs for errors
- [ ] Tested health endpoints
- [ ] Created admin user
- [ ] Set up monitoring/alerting

---

## File Locations

```
/root/showwise-security/
├── .env                          # Configuration (SECURE)
├── docker-compose.truenas.yml    # Compose file
├── docker-compose.security.yml   # Original for reference
├── setup-truenas.sh              # Automated setup script
├── ShowWise*/                    # Application source code
├── data/
│   ├── postgres/                 # Database files
│   └── redis/                    # Cache files
├── backups/                      # Database backups
└── logs/                         # Application logs
```

---

## Next Steps After Setup

1. **Configure Cloudflare** (from https://dash.cloudflare.com/)
   - Get Site Key for Turnstile
   - Get Secret Key for verification
   - Add to `.env` file

2. **Create Admin User** (via API or web interface)
   ```bash
   curl -X POST http://truenas-ip:5001/api/admin/create-user \
     -H "Authorization: Bearer YOUR_ADMIN_KEY" \
     -d '{"username":"admin","password":"secure-password"}'
   ```

3. **Test Security Features**
   ```bash
   # Test IP blocking
   curl http://truenas-ip:5001/api/ip/status/127.0.0.1
   
   # Test dashboard
   curl http://truenas-ip:5001/api/dashboard/overview
   ```

4. **Integrate with Existing Routes**
   - Use decorators on endpoints
   - Reference INTEGRATION_GUIDE.md
   - Test thoroughly

5. **Set Up Monitoring**
   - Check logs regularly
   - Set up alerts for errors
   - Monitor disk space
   - Track performance metrics

---

## For Full Details

See **TRUENAS_SETUP_GUIDE.md** for:
- Detailed step-by-step instructions
- Explanation of each step
- Advanced configuration
- Production readiness checklist
- Performance tuning tips
- Security hardening guide

---

## Support

- **Setup Issues?** → Read TRUENAS_SETUP_GUIDE.md Step 13 (Troubleshooting)
- **API Questions?** → See SECURITY_INFRASTRUCTURE.md
- **Integration Help?** → Check INTEGRATION_GUIDE.md
- **General Info?** → Read README_SECURITY.md

---

**Time to Setup**: ~15 minutes (manual) or ~5 minutes (automated)
**Storage Required**: ~50GB minimum (database, cache, backups)
**CPU/Memory**: Recommended 4GB+ RAM, 2+ cores
