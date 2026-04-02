#!/bin/bash

# ShowWise NAS Directory Setup Script
# Prepares /mnt/NAS/showwise/ for Dockge deployment

set -e

echo "=========================================="
echo "ShowWise NAS Directory Setup"
echo "=========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

NAS_PATH="/mnt/NAS/showwise"

# Check if NAS path exists
if [ ! -d "$NAS_PATH" ]; then
    echo -e "${YELLOW}[WARNING] NAS path does not exist: $NAS_PATH${NC}"
    read -p "Do you want to create it? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo mkdir -p "$NAS_PATH"
        echo -e "${GREEN}✓ Created $NAS_PATH${NC}"
    else
        echo -e "${RED}✗ NAS path required for deployment${NC}"
        exit 1
    fi
fi

# Verify write permissions
if [ ! -w "$NAS_PATH" ]; then
    echo -e "${YELLOW}[WARNING] No write permissions on $NAS_PATH${NC}"
    echo "Attempting to fix permissions with sudo..."
    sudo chmod 777 "$NAS_PATH"
    echo -e "${GREEN}✓ Permissions updated${NC}"
fi

echo ""
echo "=========================================="
echo "Creating Directory Structure"
echo "=========================================="

# Create data directories
echo -e "${BLUE}Creating database directories...${NC}"
mkdir -p "$NAS_PATH/data/security-db" "$NAS_PATH/data/organization-db" "$NAS_PATH/data/webapp-db" "$NAS_PATH/data/redis"
echo -e "${GREEN}✓ Database directories created${NC}"

# Create application directories
echo -e "${BLUE}Creating application directories...${NC}"
mkdir -p "$NAS_PATH/app/main/instance" "$NAS_PATH/app/main/uploads"
mkdir -p "$NAS_PATH/app/home/instance"
mkdir -p "$NAS_PATH/app/backend/instance"
echo -e "${GREEN}✓ Application directories created${NC}"

# Create logs directories
echo -e "${BLUE}Creating logs directories...${NC}"
mkdir -p "$NAS_PATH/logs/security-backend"
mkdir -p "$NAS_PATH/logs/main"
mkdir -p "$NAS_PATH/logs/home"
mkdir -p "$NAS_PATH/logs/backend"
echo -e "${GREEN}✓ Logs directories created${NC}"

# Create backups directory
echo -e "${BLUE}Creating backups directory...${NC}"
mkdir -p "$NAS_PATH/backups"
echo -e "${GREEN}✓ Backups directory created${NC}"

echo ""
echo "=========================================="
echo "Setting Permissions"
echo "=========================================="

# Set permissions for all directories
echo -e "${BLUE}Setting ownership and permissions...${NC}"
sudo chmod -R 777 "$NAS_PATH"
echo -e "${GREEN}✓ Permissions set to 777 (readable/writable by all)${NC}"

# If running Docker, set permissions for Docker user
if command -v docker &> /dev/null; then
    DOCKER_USER=$(id -un)
    echo -e "${BLUE}Updating permissions for Docker user: $DOCKER_USER${NC}"
    sudo chown -R "$DOCKER_USER":"$DOCKER_USER" "$NAS_PATH"
    echo -e "${GREEN}✓ Ownership updated${NC}"
fi

echo ""
echo "=========================================="
echo "Directory Structure Created"
echo "=========================================="

echo -e "${GREEN}Directory tree:${NC}"
tree -L 3 "$NAS_PATH" 2>/dev/null || find "$NAS_PATH" -type d | sort | sed 's|[^/]*/|  |g'

echo ""
echo "=========================================="
echo "Disk Space Information"
echo "=========================================="

echo -e "${BLUE}Available space on $(dirname $NAS_PATH):${NC}"
df -h "$(dirname $NAS_PATH)" | tail -1 | awk '{print "  Total: " $2 " | Used: " $3 " | Available: " $4 " | Usage: " $5}'

echo ""
echo -e "${GREEN}✓ NAS directory structure ready!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Verify the structure looks correct:"
echo "   ${BLUE}ls -la $NAS_PATH${NC}"
echo ""
echo "2. Ensure your docker-compose.dockge.yml uses these paths"
echo "   (Already configured if using the updated compose file)"
echo ""
echo "3. Start deployment:"
echo "   ${BLUE}docker-compose -f docker-compose.dockge.yml --env-file .env up -d${NC}"
echo ""
echo "4. After first run, verify data directories are populated:"
echo "   ${BLUE}ls -la $NAS_PATH/data/${NC}"
echo ""
echo -e "${YELLOW}Directory Layout:${NC}"
cat << EOF

$NAS_PATH/
├── data/                          # All database volumes
│   ├── security-db/              # Security database data
│   ├── organization-db/          # Organization database data
│   ├── webapp-db/                # WebApp database data
│   └── redis/                    # Redis cache data
├── app/                           # Application data
│   ├── main/                     # ShowWise Main App
│   │   ├── instance/             # Flask instance files
│   │   └── uploads/              # User uploads
│   ├── home/                     # ShowWise Home
│   │   └── instance/             # Flask instance files
│   └── backend/                  # ShowWise Backend
│       └── instance/             # Flask instance files
├── logs/                          # Application logs
│   ├── security-backend/         # Security backend logs
│   ├── main/                     # Main app logs
│   ├── home/                     # Home app logs
│   └── backend/                  # Backend app logs
└── backups/                       # Database backups

EOF

echo -e "${GREEN}Setup complete!${NC}"
