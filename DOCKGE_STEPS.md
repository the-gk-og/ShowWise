# ShowWise Dockge - Step by Step Setup

## Files You Need
1. **docker-compose.dockge.yml** - Main configuration (ready to use)
2. **.env** - Environment variables (copy from .env.example and fill in values)

---

## Step 1: Prepare the NAS Directory
Run this on your TrueNAS/NAS server:
```bash
# Create directory structure
mkdir -p /mnt/NAS/showwise/{data,logs,app}
mkdir -p /mnt/NAS/showwise/data/{security-db,organization-db,webapp-db,redis}
mkdir -p /mnt/NAS/showwise/logs/{security-backend,main,home,backend}
mkdir -p /mnt/NAS/showwise/app/{main,home,backend}

# Set permissions
chmod -R 755 /mnt/NAS/showwise
```

---

## Step 2: Create Environment File
On your Server:
```bash
# Copy example to actual .env
cp .env.example .env

# Edit with your values (use nano, vi, or your editor)
nano .env
```

### Must-Fill Variables in .env:
```bash
# Database Passwords (required - change these!)
SECURITY_DB_PASSWORD=your_secure_password_1
ORG_DB_PASSWORD=your_secure_password_2
WEBAPP_DB_PASSWORD=your_secure_password_3

# Secret Keys for each service (generate with: openssl rand -hex 32)
SECURITY_BACKEND_SECRET_KEY=generated_secret_1
SHOWWISE_MAIN_SECRET_KEY=generated_secret_2
SHOWWISE_HOME_SECRET_KEY=generated_secret_3
SHOWWISE_BACKEND_SECRET_KEY=generated_secret_4

# API Integration
API_INTEGRATION_KEY=your_api_key
API_INTEGRATION_SECRET=your_api_secret
ADMIN_API_KEY=your_admin_key

# Cloudflare Turnstile (get from: https://dash.cloudflare.com/)
CLOUDFLARE_TURNSTILE_SITE_KEY=your_site_key_here
CLOUDFLARE_TURNSTILE_SECRET_KEY=your_secret_key_here

# Discord (optional)
DISCORD_BOT_TOKEN=your_discord_token_here
DISCORD_GUILD_ID=your_guild_id_here
```

---

## Step 3: Access Dockge
1. Open browser: **http://your-server-ip:5001**
2. Login to Dockge (default credentials or your setup)

---

## Step 4: Create New Stack in Dockge

### In Dockge UI:
1. Click **"New Stack"** button
2. Name: `showwise-production` (or any name)
3. Choose **"Display mode"** if prompted

---

## Step 5: Add Docker Compose File

### Upload or Paste Method:
1. Select the compose editor
2. **Option A**: Paste contents of `docker-compose.dockge.yml`
3. **Option B**: Upload the file directly
4. Click **Save** or **Next**

---

## Step 6: Add Environment Variables

### In Dockge Stack Editor:
1. Look for **"Environment"** or **".env"** section
2. **Option A**: Upload your `.env` file directly
3. **Option B**: Paste each line from your `.env` file into the text area
4. Click **Save**

### Example format if pasting:
```
FLASK_ENV=production
SECURITY_DB_USER=security_user
SECURITY_DB_PASSWORD=your_password_here
API_INTEGRATION_KEY=your_key_here
CLOUDFLARE_TURNSTILE_SITE_KEY=your_key
...etc
```

---

## Step 7: Deploy

### In Dockge UI:
1. Click **"Deploy"** button
2. Monitor the deployment in real-time
3. Watch for green checkmarks ✓ on each service

---

## Step 8: Verify All Services are Running

### In Dockge UI:
1. All 7 containers should show **"Running"** (green)
2. See "Logs" tab for details if any fail
3. Cards show: `security-db`, `organization-db`, `webapp-db`, `redis`, `security-backend`, `showwise-main`, `showwise-home`, `showwise-backend`

### Via Terminal (if needed):
```bash
docker ps | grep showwise
```

---

## Step 9: Test Services

Once all are running, test endpoints:

```bash
# Main App
curl http://localhost:5000/health

# Security Backend
curl http://localhost:5001/health

# Home Page
curl http://localhost:5002/health

# Backend API
curl http://localhost:5003/health
```

All should return HTTP 200 with health status.

---

## Step 10: Configure Cloudflare Tunnel (for external access)

### In Cloudflare Dashboard:
1. Go to **Zero Trust** → **Access** → **Tunnels**
2. Select your tunnel
3. Add routes for each service:
   - `showwise.yourdomain.com` → `localhost:5000`
   - `api.yourdomain.com` → `localhost:5001`
   - `home.yourdomain.com` → `localhost:5002`
   - `backend.yourdomain.com` → `localhost:5003`

---

## What Each Service Does

| Service | Port | Purpose |
|---------|------|---------|
| **showwise-main** | 5000 | Main application (users, events, bookings) |
| **security-backend** | 5001 | IP reputation & threat detection |
| **showwise-home** | 5002 | Public landing page |
| **showwise-backend** | 5003 | Legacy/organization backend |
| **security-db** | 5432 | Security data (internal) |
| **organization-db** | 5433 | Organization data (internal) |
| **webapp-db** | 5434 | Main app data (internal) |
| **redis** | 6379 | Cache & sessions (internal) |

---

## Database Locations (on NAS)

```
/mnt/NAS/showwise/
├── data/
│   ├── security-db/          # Security database
│   ├── organization-db/       # Organization database
│   ├── webapp-db/             # Main application database
│   └── redis/                 # Redis cache
├── logs/
│   ├── security-backend/
│   ├── main/
│   ├── home/
│   └── backend/
└── app/                       # Application instance files
    ├── main/
    ├── home/
    └── backend/
```

---

## Common Issues & Solutions

### Services won't start
- Check Dockge logs in UI
- Verify `/mnt/NAS/showwise/` directory exists and has permissions
- Ensure `.env` file has all required variables

### Port already in use
- Change port mapping in docker-compose (e.g., `5010:5000` instead of `5000:5000`)
- Or use Cloudflare tunnel to avoid port conflicts

### Database connection errors
- Wait 30 seconds for databases to initialize
- Check database passwords in `.env` match docker-compose

### Logs tab errors
- Click service name in Dockge to see full logs
- Look for specific error messages
- Check `.env` values are filled correctly

---

## Useful Dockge Operations

### View Logs
- Click service → **"Logs"** tab (live view with timestamps)

### Restart Service
- Click service → **"Restart"** button

### Stop All
- Stack actions → **"Stop"**

### Update (pull latest images)
- Stack actions → **"Refresh"** or **"Pull Latest"**

### Rebuild
- Stack actions → **"Rebuild"** (rebuilds from source)

---

## Next Steps

1. ✅ Create NAS directories
2. ✅ Setup `.env` file
3. ✅ Create stack in Dockge
4. ✅ Deploy
5. ✅ Verify all running
6. ✅ Test endpoints
7. ✅ Configure Cloudflare tunnel for public access
8. ✅ Create admin users
9. ✅ Test core workflows

---

## Helpful Commands

```bash
# SSH to server and check containers
docker ps

# View specific service logs
docker logs showwise-main -f

# Connect to database
psql -h localhost -p 5432 -U security_user -d security_db

# Check disk usage
df -h /mnt/NAS/showwise

# Check NAS mount
mount | grep NAS
```

---

**Need Help?**
- Check Dockge Logs tab
- Review Docker logs from terminal
- Verify `.env` file variables
- Ensure NAS path `/mnt/NAS/showwise/` exists
- Check file permissions: `chmod 755 /mnt/NAS/showwise`
