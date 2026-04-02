# ShowWise Dockge Deployment - NAS Configuration Summary

## Changes Made

Your `docker-compose.dockge.yml` has been updated to use `/mnt/NAS/showwise/` as the persistent storage volume for all databases, application data, and logs.

---

## NAS Volume Structure

All data will be stored in the following structure:

```
/mnt/NAS/showwise/
├── data/                              # Database volumes
│   ├── security-db/                  # Security database
│   ├── organization-db/              # Organization database  
│   ├── webapp-db/                    # Main webapp database
│   └── redis/                        # Redis cache data
│
├── app/                               # Application instance files
│   ├── main/
│   │   ├── instance/                 # Flask instance files
│   │   └── uploads/                  # User uploads
│   ├── home/
│   │   └── instance/                 # Flask instance files
│   └── backend/
│       └── instance/                 # Flask instance files
│
├── logs/                              # Service logs
│   ├── security-backend/
│   ├── main/
│   ├── home/
│   └── backend/
│
└── backups/                           # Location for DB backups
```

---

## Volume Mappings by Service

| Service | Container Path | NAS Path |
|---------|-----------------|----------|
| security-db | `/var/lib/postgresql/data` | `/mnt/NAS/showwise/data/security-db` |
| organization-db | `/var/lib/postgresql/data` | `/mnt/NAS/showwise/data/organization-db` |
| webapp-db | `/var/lib/postgresql/data` | `/mnt/NAS/showwise/data/webapp-db` |
| redis | `/data` | `/mnt/NAS/showwise/data/redis` |
| security-backend | `/app/logs` | `/mnt/NAS/showwise/logs/security-backend` |
| showwise-main | `/app/instance`, `/app/uploads`, `/app/logs` | `/mnt/NAS/showwise/app/main/instance`, `/app/main/uploads`, `/logs/main` |
| showwise-home | `/app/instance`, `/app/logs` | `/mnt/NAS/showwise/app/home/instance`, `/logs/home` |
| showwise-backend | `/app/instance`, `/app/logs` | `/mnt/NAS/showwise/app/backend/instance`, `/logs/backend` |

---

## Pre-Deployment Setup

### Option 1: Automated (Recommended)

```bash
# Run the NAS setup script
chmod +x setup-nas-directory.sh
./setup-nas-directory.sh
```

This will:
- ✅ Create all required directories
- ✅ Set proper permissions (777)
- ✅ Display directory structure
- ✅ Show available disk space

### Option 2: Manual Setup

```bash
# Create base directory (if it doesn't exist)
mkdir -p /mnt/NAS/showwise

# Create all subdirectories
mkdir -p /mnt/NAS/showwise/data/{security-db,organization-db,webapp-db,redis}
mkdir -p /mnt/NAS/showwise/app/{main/{instance,uploads},home/instance,backend/instance}
mkdir -p /mnt/NAS/showwise/logs/{security-backend,main,home,backend}
mkdir -p /mnt/NAS/showwise/backups

# Set permissions (so Docker can write)
chmod -R 777 /mnt/NAS/showwise

# Optional: Set proper ownership for Docker user
sudo chown -R 1000:1000 /mnt/NAS/showwise  # Adjust UID/GID as needed
```

---

## Deployment Steps

### 1. Prepare NAS Storage
```bash
./setup-nas-directory.sh
```

### 2. Prepare Environment File
```bash
./setup-dockge.sh
```

### 3. Deploy with Docker Compose
```bash
docker-compose -f docker-compose.dockge.yml --env-file .env up -d
```

### 4. Verify Deployment
```bash
# Check all services are running
docker-compose -f docker-compose.dockge.yml ps

# Check NAS data is being written
ls -la /mnt/NAS/showwise/data/
```

---

## Monitoring NAS Storage

### Check Used Space
```bash
# Overall usage
du -sh /mnt/NAS/showwise/

# Per component
du -sh /mnt/NAS/showwise/{data,app,logs,backups}

# Per database
du -sh /mnt/NAS/showwise/data/*
```

### Monitor I/O Performance
```bash
# Real-time I/O stats (if available)
iostat -x 1

# Or use iotop
iotop
```

---

## Backup Strategy

With NAS storage at `/mnt/NAS/showwise/`, backups are easier:

### Quick Backup (Copy entire /mnt/NAS/showwise/)
```bash
# Backup entire NAS showwise directory
tar -czf /backup/showwise_$(date +%Y%m%d_%H%M%S).tar.gz /mnt/NAS/showwise/

# Or using rsync for incremental backups
rsync -av /mnt/NAS/showwise/ /backup/showwise-$(date +%Y%m%d)/
```

### Database-Specific Backups
```bash
# Backup security-db
docker-compose -f docker-compose.dockge.yml exec -T security-db \
  pg_dump -U security_user security_db | \
  gzip > /mnt/NAS/showwise/backups/security_db_$(date +%Y%m%d_%H%M%S).sql.gz

# Similar for organization-db and webapp-db
```

---

## Key Points for TrueNAS/NAS Setup

1. **Permissions**: Docker needs write access to `/mnt/NAS/showwise/`
   - Run: `chmod 777 /mnt/NAS/showwise/`

2. **Network Mounts**: If NAS is network-mounted:
   - Verify mount is active: `mount | grep showwise`
   - Check timeout settings
   - Monitor for disconnections in `/var/log/syslog`

3. **Performance**: NAS I/O is slower than local storage
   - Monitor logs for slow queries
   - Consider adding read replicas for scale
   - Plan capacity accordingly

4. **Data Persistence**: Data survives container restarts
   - Volumes will persist even if containers are removed
   - Always backup before major updates

5. **Filesystem**: Ensure NAS supports:
   - POSIX permissions
   - PostgreSQL requirements (fsync, etc.)
   - File locking

---

## Troubleshooting NAS Issues

### Permission Denied Errors
```bash
# Check current permissions
ls -la /mnt/NAS/showwise/

# Fix permissions
sudo chmod 777 /mnt/NAS/showwise/ -R

# Or set specific Docker user
sudo chown -R $(id -u):$(id -g) /mnt/NAS/showwise/
```

### NAS Mount Not Available
```bash
# Check if mount exists
mount | grep /mnt/NAS/showwise

# Remount NAS
sudo mount -a

# Or remount specific
sudo mount /mnt/NAS/showwise
```

### Database Won't Start
```bash
# Check logs
docker-compose -f docker-compose.dockge.yml logs security-db

# Verify NAS path exists and is writable
touch /mnt/NAS/showwise/test.txt && rm /mnt/NAS/showwise/test.txt

# Check disk space
df -h /mnt/NAS/showwise
```

### Slow Performance
```bash
# Monitor I/O
iostat -x 1 10

# Check disk usage
du -sh /mnt/NAS/showwise/data/*

# Consider reducing log verbosity
# Check service logs for slow queries
```

---

## Upgrading/Migrating

When updating containers with NAS volumes:

```bash
# 1. Stop services
docker-compose -f docker-compose.dockge.yml stop

# 2. Backup data on NAS
cp -r /mnt/NAS/showwise /mnt/NAS/showwise_backup_$(date +%Y%m%d)

# 3. Rebuild and start
docker-compose -f docker-compose.dockge.yml up -d --build

# 4. Run migrations if needed
docker-compose -f docker-compose.dockge.yml exec showwise-main flask db upgrade
```

---

## Performance Optimization Tips

1. **Enable NAS Caching** (if applicable):
   - Check NAS settings for read/write cache
   - May need to be disabled for safety with databases

2. **Monitor Database Query Performance**:
   - Enable slow query logs
   - Tune PostgreSQL parameters in environment
   - Add indexes for frequent queries

3. **Local Cache with Redis**:
   - Redis is on NAS (`/mnt/NAS/showwise/data/redis`)
   - Consider separate fast storage if performance critical
   - Monitor Redis memory usage

4. **Separate Logs**:
   - Logs are on NAS at `/mnt/NAS/showwise/logs`
   - Consider separate log storage if high volume
   - Implement log rotation

---

## Files Updated/Created

| File | Purpose |
|------|---------|
| `docker-compose.dockge.yml` | ✅ Updated - Now uses `/mnt/NAS/showwise/` |
| `setup-nas-directory.sh` | ✅ New - Automates NAS directory prep |
| `.env.example` | Uses existing config (no changes needed) |

---

## Quick Deployment Checklist

- [ ] NAS mount point exists and is accessible
- [ ] Ran `./setup-nas-directory.sh` to create structure
- [ ] Ran `./setup-dockge.sh` to setup environment
- [ ] Verified `.env` has all required values
- [ ] Run `docker-compose -f docker-compose.dockge.yml up -d`
- [ ] Check services are healthy: `docker-compose -f docker-compose.dockge.yml ps`
- [ ] Verify data written to NAS: `ls /mnt/NAS/showwise/data/`
- [ ] Monitor logs for errors: `docker-compose -f docker-compose.dockge.yml logs -f`

---

**Configuration Date**: March 31, 2026  
**NAS Storage**: `/mnt/NAS/showwise/`  
**Deployment Type**: TrueNAS / Network-Attached Storage
