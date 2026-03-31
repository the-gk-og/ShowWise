#!/bin/bash

# ============================================
# ShowWise Security Infrastructure
# TrueNAS Automated Setup Script
# ============================================

echo "🚀 ShowWise Security Infrastructure - TrueNAS Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}❌ This script must be run as root${NC}"
   exit 1
fi

# ============================================
# Step 1: Check Prerequisites
# ============================================
echo -e "${BLUE}Step 1: Checking Prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check Git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠ Git not found. Installing Git...${NC}"
    apt-get update && apt-get install -y git
fi
echo -e "${GREEN}✓ Git installed${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠ Python3 not found. Installing Python3...${NC}"
    apt-get update && apt-get install -y python3
fi
echo -e "${GREEN}✓ Python3 installed${NC}"

echo ""

# ============================================
# Step 2: Get GitHub Repository URL
# ============================================
echo -e "${BLUE}Step 2: Configure GitHub Repository${NC}"
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/Active-ShowWise.git): " GITHUB_URL

# Validate URL
if [[ ! $GITHUB_URL =~ ^https://github.com/.*/.*\.git$ ]]; then
    echo -e "${RED}❌ Invalid GitHub URL. Please use format: https://github.com/username/repo.git${NC}"
    exit 1
fi
echo -e "${GREEN}✓ GitHub URL set: $GITHUB_URL${NC}"

echo ""

# ============================================
# Step 3: Create Directory Structure
# ============================================
echo -e "${BLUE}Step 3: Creating Directory Structure...${NC}"

PROJECT_DIR="/root/showwise-security"
mkdir -p "$PROJECT_DIR/data/postgres"
mkdir -p "$PROJECT_DIR/data/redis"
mkdir -p "$PROJECT_DIR/backups"
mkdir -p "$PROJECT_DIR/logs"

chmod 755 "$PROJECT_DIR"
chmod 777 "$PROJECT_DIR/data"/*
chmod 777 "$PROJECT_DIR/logs"
chmod 777 "$PROJECT_DIR/backups"

echo -e "${GREEN}✓ Directory structure created at: $PROJECT_DIR${NC}"

echo ""

# ============================================
# Step 4: Clone Repository
# ============================================
echo -e "${BLUE}Step 4: Cloning Repository from GitHub...${NC}"

cd "$PROJECT_DIR"

# Check if directory is empty
if [ -z "$(ls -A $PROJECT_DIR)" ]; then
    git clone "$GITHUB_URL" .
else
    echo -e "${YELLOW}⚠ Directory not empty. Running git pull instead...${NC}"
    git pull origin main
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to clone repository. Check your GitHub URL and permissions.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Repository cloned successfully${NC}"

echo ""

# ============================================
# Step 5: Generate Security Keys
# ============================================
echo -e "${BLUE}Step 5: Generating Security Keys...${NC}"

API_KEY=$(python3 << 'EOF'
import secrets
print(secrets.token_urlsafe(32))
EOF
)

API_SECRET=$(python3 << 'EOF'
import secrets
print(secrets.token_urlsafe(32))
EOF
)

ADMIN_KEY=$(python3 << 'EOF'
import secrets
print(secrets.token_urlsafe(32))
EOF
)

SECURITY_SECRET=$(python3 << 'EOF'
import secrets
print(secrets.token_urlsafe(32))
EOF
)

SHOWWISE_SECRET=$(python3 << 'EOF'
import secrets
print(secrets.token_urlsafe(32))
EOF
)

HOME_SECRET=$(python3 << 'EOF'
import secrets
print(secrets.token_urlsafe(32))
EOF
)

BACKEND_SECRET=$(python3 << 'EOF'
import secrets
print(secrets.token_urlsafe(32))
EOF
)

echo -e "${GREEN}✓ Security keys generated${NC}"

echo ""

# ============================================
# Step 6: Get Cloudflare Credentials
# ============================================
echo -e "${BLUE}Step 6: Cloudflare Turnstile Configuration${NC}"
echo "Go to: https://dash.cloudflare.com/profile/settings/overview"
echo "Navigate to: Turnstile → Add site"
echo ""
read -p "Enter Cloudflare Turnstile Site Key (or press Enter to skip): " CF_SITE_KEY
read -p "Enter Cloudflare Turnstile Secret (or press Enter to skip): " CF_SECRET

if [ -z "$CF_SITE_KEY" ]; then
    CF_SITE_KEY="your-turnstile-site-key"
    CF_SECRET="your-turnstile-secret"
    echo -e "${YELLOW}⚠ Cloudflare credentials not set. Update .env later.${NC}"
fi

echo ""

# ============================================
# Step 7: Create .env File
# ============================================
echo -e "${BLUE}Step 7: Creating .env Configuration File...${NC}"

cat > "$PROJECT_DIR/.env" << EOF
# ==================================
# Security Backend Configuration
# ==================================
SECURITY_SECRET_KEY=$SECURITY_SECRET
SECURITY_DATABASE_URL=postgresql://security_user:securepassword123!@security-db:5432/security_db
API_INTEGRATION_KEY=$API_KEY
API_INTEGRATION_SECRET=$API_SECRET
ADMIN_API_KEY=$ADMIN_KEY
REDIS_URL=redis://redis:6379/0

# ==================================
# ShowWise Main App Configuration
# ==================================
SHOWWISE_SECRET_KEY=$SHOWWISE_SECRET
DATABASE_URL=postgresql://showwise_user:showwisepass456!@security-db:5432/showwise_db
APP_INSTANCE_NAME=main
CLOUDFLARE_SITE_KEY=$CF_SITE_KEY
CLOUDFLARE_SECRET=$CF_SECRET

# ==================================
# ShowWise Home Configuration
# ==================================
HOME_SECRET_KEY=$HOME_SECRET
APP_INSTANCE_NAME=home

# ==================================
# ShowWise Backend Configuration
# ==================================
BACKEND_SECRET_KEY=$BACKEND_SECRET

# ==================================
# PostgreSQL Configuration
# ==================================
POSTGRES_USER=security_user
POSTGRES_PASSWORD=securepassword123!
POSTGRES_DB=security_db

# ==================================
# Cloudflare Turnstile
# ==================================
CLOUDFLARE_TURNSTILE_SITE_KEY=$CF_SITE_KEY
CLOUDFLARE_TURNSTILE_SECRET=$CF_SECRET
EOF

chmod 600 "$PROJECT_DIR/.env"
echo -e "${GREEN}✓ .env file created successfully${NC}"

echo ""

# ============================================
# Step 8: Build Docker Images
# ============================================
echo -e "${BLUE}Step 8: Building Docker Images...${NC}"
echo "This may take 5-10 minutes..."

cd "$PROJECT_DIR"

# Check if docker-compose.truenas.yml exists, if not create it
if [ ! -f "docker-compose.truenas.yml" ]; then
    echo -e "${YELLOW}⚠ docker-compose.truenas.yml not found. Creating it...${NC}"
    # The user should already have this from GitHub, but just in case
    cp docker-compose.security.yml docker-compose.truenas.yml 2>/dev/null || true
fi

docker-compose -f docker-compose.truenas.yml build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Docker image build failed. Check the logs above.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker images built successfully${NC}"

echo ""

# ============================================
# Step 9: Start Services
# ============================================
echo -e "${BLUE}Step 9: Starting Services...${NC}"

docker-compose -f docker-compose.truenas.yml up -d

echo -e "${GREEN}✓ Services starting...${NC}"
echo "Waiting for services to be healthy (this may take 30 seconds)..."

# Wait for services
sleep 30

echo ""

# ============================================
# Step 10: Verify Services
# ============================================
echo -e "${BLUE}Step 10: Verifying Services...${NC}"

docker-compose -f docker-compose.truenas.yml ps

echo ""

# Check health endpoints
echo "Testing health endpoints..."

if curl -s http://localhost:5001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Security Backend (port 5001) is healthy${NC}"
else
    echo -e "${YELLOW}⚠ Security Backend not yet healthy (may still be starting)${NC}"
fi

if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ShowWise Main (port 5000) is healthy${NC}"
else
    echo -e "${YELLOW}⚠ ShowWise Main not yet healthy (may still be starting)${NC}"
fi

echo ""

# ============================================
# Step 11: Display Summary
# ============================================
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✓ Setup Complete!                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"

echo ""
echo -e "${BLUE}Access Your Services:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Security Backend:  http://localhost:5001"
echo -e "  ShowWise Main:     http://localhost:5000"
echo -e "  ShowWise Home:     http://localhost:5002"
echo -e "  ShowWise Backend:  http://localhost:5003"
echo -e "  PostgreSQL:        localhost:5432"
echo -e "  Redis:             localhost:6379"
echo ""

echo -e "${BLUE}Project Directory:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  $PROJECT_DIR"
echo ""

echo -e "${BLUE}Configuration File:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  $PROJECT_DIR/.env"
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  View logs:       docker-compose -f docker-compose.truenas.yml logs -f"
echo "  Stop services:   docker-compose -f docker-compose.truenas.yml stop"
echo "  Restart stack:   docker-compose -f docker-compose.truenas.yml restart"
echo "  Update from Git: cd $PROJECT_DIR && git pull"
echo "  Backup DB:       docker-compose -f docker-compose.truenas.yml exec security-db pg_dump -U security_user -d security_db > backups/backup.sql"
echo ""

echo -e "${YELLOW}⚠️  Important Next Steps:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. Update Cloudflare credentials in .env if not set"
echo "  2. Change database passwords in .env for production"
echo "  3. Set up SSL/TLS with a reverse proxy"
echo "  4. Configure firewall rules"
echo "  5. Set up automated backups"
echo "  6. Review and integrate with existing routes"
echo ""

echo -e "${GREEN}For more details, see: TRUENAS_SETUP_GUIDE.md${NC}"
echo ""
