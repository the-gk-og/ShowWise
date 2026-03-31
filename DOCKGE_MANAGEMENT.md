# 🐳 ShowWise Docker Stack - Management via Dockge UI

**Manage your entire ShowWise security infrastructure through an easy-to-use web interface**

---

## 📋 What is Dockge?

Dockge is a modern, simple, yet powerful Docker container management UI that runs in Docker. It allows you to:
- ✅ Manage Docker Compose stacks via web UI
- ✅ View container logs in real-time
- ✅ Start/stop/restart containers
- ✅ Monitor resource usage
- ✅ Deploy/update stacks
- ✅ Edit compose files directly
- ✅ No CLI needed

---

## 🚀 Step 1: Install Dockge on TrueNAS

### Option A: Quick Install (Recommended)

```bash
# SSH into TrueNAS
ssh root@your-truenas-ip

# Create Dockge directory
mkdir -p /root/dockge
cd /root/dockge

# Create docker-compose.yml for Dockge
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  dockge:
    image: louislam/dockge:latest
    restart: unless-stopped
    ports:
      - "5173:5173"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data:/app/data
      - /root/showwise-security:/app/stacks/showwise-security
    environment:
      DOCKGE_STACKS_DIR: /app/stacks

volumes:
  dockge_data:
EOF

# Start Dockge
docker-compose up -d

# Wait for it to start
sleep 10

# Check status
docker-compose ps
```

### Access Dockge Web UI

Open your browser:
```
http://truenas-ip:5173
```

**Default login:**
- Username: `admin`
- Password: `admin` (change immediately!)

---

## 🐳 Step 2: Add ShowWise Stack to Dockge

### Method 1: Via Web UI (Easiest)

1. **Open Dockge**: http://truenas-ip:5173
2. **Click**: "Compose" in left sidebar
3. **Click**: "Add new Compose File"
4. **Enter Name**: `showwise-security`
5. **Select Directory**: `/app/stacks/showwise-security`
6. **Click**: "Create"

Dockge will automatically detect your `docker-compose.truenas.yml`

### Method 2: Manual Configuration

```bash
# Copy your compose file to Dockge stacks directory
cp /root/showwise-security/docker-compose.truenas.yml \
   /root/dockge/data/stacks/showwise-security/docker-compose.yml

# Dockge will detect it automatically
```

---

## 🎯 Step 3: Deploy Stack from Dockge UI

### Deploy Your ShowWise Stack

1. **Open Dockge**: http://truenas-ip:5173
2. **Click**: "Compose" → "showwise-security"
3. **Click**: "Deploy"
4. **Watch**: Build progress in real-time
5. **Verify**: All 6 services show "Running" with green status

### Stack Deployment Progress

Dockge shows:
```
Building images...
  ✓ security-backend built
  ✓ showwise-main built
  ✓ showwise-home built
  ✓ showwise-backend built

Starting containers...
  ✓ security-db started (healthy)
  ✓ redis started (healthy)
  ✓ security-backend started (healthy)
  ✓ showwise-main started (healthy)
  ✓ showwise-home started (healthy)
  ✓ showwise-backend started (healthy)
```

---

## 📊 Step 4: Monitor Stack via Dockge

### View Running Containers

1. **Click**: "Containers" in sidebar
2. **See**: List of all running containers with:
   - Status (green = healthy, yellow = unhealthy, red = stopped)
   - CPU usage
   - Memory usage
   - Uptime

### Container Status Colors

| Color | Meaning |
|-------|---------|
| 🟢 Green | Running and healthy |
| 🟡 Yellow | Running but unhealthy |
| 🔴 Red | Stopped or failed |
| ⚫ Gray | Not running |

### Monitor Resources

1. **Click**: Container name (e.g., "showwise-security_security-backend_1")
2. **See**: Real-time stats:
   - CPU percentage
   - Memory usage
   - Network I/O
   - Uptime

---

## 📝 Step 5: View Logs in Dockge

### Real-Time Logs

1. **Click**: Container name
2. **Click**: "Logs" tab
3. **See**: Live streaming logs
4. **Options**:
   - Download logs
   - Copy logs
   - Auto-scroll
   - Filter by level

### View Logs for All Services

```
Container Logs:

security-db:
  LOG: database initialized
  LOG: ready to accept connections

redis:
  LOG: Redis server started
  LOG: Ready to accept connections

security-backend:
  LOG: Building Flask app...
  LOG: Starting Gunicorn...
  
showwise-main:
  LOG: Connecting to security backend...
  LOG: Application started
```

---

## 🎮 Step 6: Manage Containers via Dockge UI

### Control Individual Containers

**Right-click any container:**
- ▶️ Start
- ⏸️ Stop
- 🔄 Restart
- 🗑️ Remove
- 📋 Inspect
- 📊 Stats

**Example: Restart Security Backend**
1. Click "Containers"
2. Find "showwise-security_security-backend_1"
3. Right-click → "Restart"
4. Watch status change to green when ready

### Restart Entire Stack

1. **Click**: "Compose" → "showwise-security"
2. **Click**: "Actions" → "Restart"
3. All 6 containers restart in sequence

---

## ⬆️ Step 7: Update Stack from GitHub

### Update Using Dockge UI

1. **Click**: "Compose" → "showwise-security"
2. **Click**: "Actions" → "Pull and Deploy"
3. Dockge automatically:
   - Pulls latest from GitHub
   - Rebuilds images
   - Restarts containers

### Or Manual Update

```bash
cd /root/showwise-security
git pull origin main

# Then in Dockge UI:
# Click "Compose" → "showwise-security" → "Deploy"
```

---

## 💾 Step 8: Backup via Dockge

### Export Stack Configuration

1. **Click**: "Compose" → "showwise-security"
2. **Click**: "Actions" → "Export"
3. Downloads `docker-compose.yml` backup

### Backup Database

```bash
# SSH into TrueNAS
docker-compose -f /root/showwise-security/docker-compose.truenas.yml exec security-db \
  pg_dump -U security_user -d security_db > \
  /root/showwise-security/backups/backup-$(date +%Y%m%d-%H%M%S).sql
```

---

## 🔧 Step 9: Edit Compose File in Dockge

### Modify Configuration

1. **Click**: "Compose" → "showwise-security"
2. **Click**: "Edit"
3. **Modify**: docker-compose.yml directly
4. **Click**: "Save"
5. **Click**: "Deploy" to apply changes

### Example: Change Port

```yaml
# Before:
security-backend:
  ports:
    - "5001:5000"

# After (if you want to change port):
security-backend:
  ports:
    - "5011:5000"  # Changed port from 5001 to 5011

# Click "Save" and "Deploy"
```

---

## 🔒 Step 10: Security & Administration

### Change Admin Password

1. **Click**: User icon (top right)
2. **Click**: "Settings"
3. **Click**: "Change Password"
4. **Enter**: New password
5. **Click**: "Update"

### Backup Dockge Configuration

```bash
# Backup Dockge data
tar -czf /root/backups/dockge-backup-$(date +%Y%m%d).tar.gz \
  /root/dockge/data/

# This backs up all stacks and configuration
```

---

## 📊 Dashboard Overview

Dockge main dashboard shows:

```
╔════════════════════════════════════════╗
║    Dockge - Container Management      ║
╚════════════════════════════════════════╝

┌─ System Status ─────────────────────┐
│ Docker Version: 24.0.0              │
│ Containers: 6 total, 6 running      │
│ Disk Usage: 45GB / 500GB (9%)       │
└─────────────────────────────────────┘

┌─ Stacks ────────────────────────────┐
│ ✓ showwise-security (6 containers)  │
│   └─ All services healthy           │
└─────────────────────────────────────┘

┌─ Resource Usage ────────────────────┐
│ CPU:    12% (2 cores @ 2.4GHz)     │
│ Memory: 4.2GB / 16GB (26%)         │
│ Disk I/O: 45MB/s read, 12MB/s write│
└─────────────────────────────────────┘
```

---

## 🌐 Dockge Web UI Features

| Feature | Location | Use |
|---------|----------|-----|
| **Containers** | Sidebar | View & manage all containers |
| **Compose** | Sidebar | Manage stacks |
| **Status** | Dashboard | System & stack status |
| **Logs** | Container Detail | View container logs |
| **Stats** | Container Detail | CPU, memory, network |
| **Terminal** | Container Detail | SSH into container |
| **Actions** | Stack Menu | Deploy, restart, update |

---

## 🚀 Quick Reference - Common Tasks

### Start Stack
1. Click "Compose" → "showwise-security"
2. Click "Deploy"

### View All Logs
1. Click "Containers"
2. Select any container
3. Tab: "Logs"

### Restart Service
1. Click "Containers"
2. Right-click container
3. Select "Restart"

### Update from GitHub
1. Click "Compose" → "showwise-security"
2. Click "Actions" → "Pull and Deploy"

### Monitor Resources
1. Click "Containers"
2. Container shows real-time stats (CPU, memory, network)

### Backup Stack
1. Click "Compose" → "showwise-security"
2. Click "Actions" → "Export"

---

## 📋 Troubleshooting in Dockge

### Container Shows Red (Not Running)

1. Click container name
2. Click "Logs" tab
3. Read error message
4. Click "Restart" button
5. Wait 30 seconds
6. Check logs again

### Stack Deploy Failed

1. Click "Compose" → "showwise-security"
2. Click "Edit"
3. Check for syntax errors (highlighted in red)
4. Verify .env variables are correct
5. Click "Deploy" again

### Out of Memory

1. Dashboard shows memory usage
2. Click "Containers"
3. Right-click heavy container
4. Select "Remove"
5. Free up space
6. Click "Deploy" to recreate

---

## 🔗 Access Services from Dockge

Once deployed, click "Compose" → "showwise-security" to see all services:

| Service | Port | Click to Open |
|---------|------|---------------|
| Security Backend | 5001 | http://localhost:5001 |
| ShowWise Main | 5000 | http://localhost:5000 |
| ShowWise Home | 5002 | http://localhost:5002 |
| ShowWise Backend | 5003 | http://localhost:5003 |
| Dockge | 5173 | http://localhost:5173 |

---

## 🎯 Complete Workflow Example

### Deploy → Monitor → Update

**Day 1: Initial Deployment**
```
1. Open Dockge: http://truenas-ip:5173
2. Add showwise-security compose file
3. Click "Deploy"
4. Wait for all containers to show green
5. Verify logs show no errors
```

**Daily: Monitor**
```
1. Click "Containers"
2. Check all containers are green & healthy
3. Monitor resource usage (CPU, memory)
4. Check logs for any warnings
```

**Weekly: Backup**
```
1. Click "Compose" → "showwise-security" → "Export"
2. Save backup
```

**On Update: Pull & Deploy**
```
1. Click "Compose" → "showwise-security"
2. Click "Pull and Deploy"
3. Watch build progress
4. Verify all containers restart successfully
```

---

## 📞 Dockge vs Command Line

| Task | CLI | Dockge UI |
|------|-----|-----------|
| View status | `docker ps` | Click "Containers" |
| View logs | `docker logs <container>` | Click container → "Logs" |
| Restart container | `docker restart <id>` | Right-click → "Restart" |
| Deploy stack | `docker-compose up -d` | Click "Deploy" |
| Update from GitHub | `git pull && rebuild` | Click "Pull and Deploy" |
| Monitor resources | `docker stats` | Dashboard or container stats |
| Edit config | Terminal editor | Click "Edit" in UI |

**Dockge UI is simpler and more visual for most operations!**

---

## ✅ Setup Complete!

Your ShowWise stack is now manageable via Dockge web UI:

✅ Deploy/restart/stop via clicks
✅ Monitor all containers in real-time
✅ View logs with beautiful UI
✅ Track resource usage visually
✅ Update from GitHub easily
✅ No CLI needed (unless you want to)
✅ Backup stack configuration

---

## 🔗 Quick Links

- **Dockge UI**: http://truenas-ip:5173
- **Security Backend**: http://truenas-ip:5001
- **ShowWise Main**: http://truenas-ip:5000
- **ShowWise Home**: http://truenas-ip:5002
- **Dashboard**: http://truenas-ip:5001/api/dashboard/overview

---

## 📖 Next Steps

1. **Open Dockge**: http://truenas-ip:5173
2. **Change Admin Password**: Click user icon → Settings
3. **Verify Stack**: Click "Containers" - all should show green
4. **Check Logs**: Click any container → "Logs"
5. **Monitor Resources**: Dashboard shows CPU, memory, disk
6. **Bookmark this page** for easy access

---

**Now manage your entire ShowWise security infrastructure with just a few clicks! 🎉**
