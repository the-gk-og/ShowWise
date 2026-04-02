#!/bin/bash

# ShowWise Dockge Deployment Setup Script
# This script automates the initial setup for Dockge deployment

set -e

echo "=========================================="
echo "ShowWise Dockge Deployment Setup"
echo "=========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}[WARNING] .env file already exists. Backing up to .env.backup${NC}"
    cp .env .env.backup
else
    echo -e "${GREEN}[INFO] Creating .env file from template${NC}"
    cp .env.example .env
fi

# Function to generate secure secret
generate_secret() {
    openssl rand -hex 32
}

# Function to prompt and get user input
prompt_input() {
    local prompt_text=$1
    local default_value=$2
    local response
    
    if [ -z "$default_value" ]; then
        read -p "$(echo -e ${YELLOW}$prompt_text${NC}): " response
    else
        read -p "$(echo -e ${YELLOW}$prompt_text${NC}) [$default_value]: " response
        response=${response:-$default_value}
    fi
    echo $response
}

# Main setup
echo ""
echo "=========================================="
echo "Step 1: Generate Secure Secrets"
echo "=========================================="
echo -e "${YELLOW}Generating secure random secrets...${NC}"

SECURITY_SECRET=$(generate_secret)
MAIN_SECRET=$(generate_secret)
HOME_SECRET=$(generate_secret)
BACKEND_SECRET=$(generate_secret)

echo -e "${GREEN}✓ Secrets generated${NC}"

echo ""
echo "=========================================="
echo "Step 2: Database Passwords"
echo "=========================================="

SECURITY_DB_PASS=$(prompt_input "Security DB Password" "$(openssl rand -base64 12)")
ORG_DB_PASS=$(prompt_input "Organization DB Password" "$(openssl rand -base64 12)")
WEBAPP_DB_PASS=$(prompt_input "WebApp DB Password" "$(openssl rand -base64 12)")

echo ""
echo "=========================================="
echo "Step 3: API Keys"
echo "=========================================="

API_KEY=$(prompt_input "API Integration Key" "$(openssl rand -hex 16)")
API_SECRET=$(prompt_input "API Integration Secret" "$(openssl rand -hex 32)")
ADMIN_KEY=$(prompt_input "Admin API Key" "$(openssl rand -hex 16)")

echo ""
echo "=========================================="
echo "Step 4: Cloudflare Turnstile (Bot Protection)"
echo "=========================================="
echo -e "${YELLOW}Get these from: https://dash.cloudflare.com/profile/tokens${NC}"

TURNSTILE_SITE=$(prompt_input "Cloudflare Turnstile Site Key" "")
TURNSTILE_SECRET=$(prompt_input "Cloudflare Turnstile Secret Key" "")

echo ""
echo "=========================================="
echo "Step 5: Optional - Discord Integration"
echo "=========================================="
echo -e "${YELLOW}Leave blank to skip. Get Discord token from Discord Developer Portal${NC}"

DISCORD_TOKEN=$(prompt_input "Discord Bot Token (optional)" "")
DISCORD_GUILD=$(prompt_input "Discord Guild ID (optional)" "")

echo ""
echo "=========================================="
echo "Updating .env file..."
echo "=========================================="

# Update .env file with values
update_env() {
    local key=$1
    local value=$2
    # Escape special characters in value
    value=$(echo "$value" | sed -e 's/[\/&]/\\&/g')
    sed -i "s/${key}=.*/${key}=${value}/g" .env
}

# Update secrets
update_env "SECURITY_BACKEND_SECRET_KEY" "$SECURITY_SECRET"
update_env "SHOWWISE_MAIN_SECRET_KEY" "$MAIN_SECRET"
update_env "SHOWWISE_HOME_SECRET_KEY" "$HOME_SECRET"
update_env "SHOWWISE_BACKEND_SECRET_KEY" "$BACKEND_SECRET"

# Update database passwords
update_env "SECURITY_DB_PASSWORD" "$SECURITY_DB_PASS"
update_env "ORG_DB_PASSWORD" "$ORG_DB_PASS"
update_env "WEBAPP_DB_PASSWORD" "$WEBAPP_DB_PASS"

# Update API keys
update_env "API_INTEGRATION_KEY" "$API_KEY"
update_env "API_INTEGRATION_SECRET" "$API_SECRET"
update_env "ADMIN_API_KEY" "$ADMIN_KEY"

# Update Cloudflare
if [ ! -z "$TURNSTILE_SITE" ]; then
    update_env "CLOUDFLARE_TURNSTILE_SITE_KEY" "$TURNSTILE_SITE"
fi
if [ ! -z "$TURNSTILE_SECRET" ]; then
    update_env "CLOUDFLARE_TURNSTILE_SECRET_KEY" "$TURNSTILE_SECRET"
fi

# Update Discord (optional)
if [ ! -z "$DISCORD_TOKEN" ]; then
    update_env "DISCORD_BOT_TOKEN" "$DISCORD_TOKEN"
fi
if [ ! -z "$DISCORD_GUILD" ]; then
    update_env "DISCORD_GUILD_ID" "$DISCORD_GUILD"
fi

echo -e "${GREEN}✓ .env file updated${NC}"

echo ""
echo "=========================================="
echo "Step 6: Verify Docker & Docker Compose"
echo "=========================================="

if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed$(docker --version)${NC}"
else
    echo -e "${RED}✗ Docker is NOT installed${NC}"
    echo "   Install from: https://docs.docker.com/install/"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose is installed ($(docker-compose --version))${NC}"
else
    echo -e "${RED}✗ Docker Compose is NOT installed${NC}"
    echo "   Install from: https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Review/edit .env file:"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Start the Dockge deployment:"
echo "   ${YELLOW}docker-compose -f docker-compose.dockge.yml --env-file .env up -d${NC}"
echo ""
echo "3. Monitor the deployment:"
echo "   ${YELLOW}docker-compose -f docker-compose.dockge.yml logs -f${NC}"
echo ""
echo "4. Verify services are healthy:"
echo "   ${YELLOW}docker-compose -f docker-compose.dockge.yml ps${NC}"
echo ""
echo -e "${YELLOW}Service URLs after deployment:${NC}"
echo "  • ShowWise Main: http://localhost:5000"
echo "  • ShowWise Home: http://localhost:5002"
echo "  • Security Backend: http://localhost:5001"
echo "  • ShowWise Backend: http://localhost:5003"
echo ""
echo -e "${YELLOW}For more information, see: DOCKGE_DEPLOYMENT_GUIDE.md${NC}"
echo ""

# Create backup of setup for reference
echo "=========================================="
echo "Saving configuration summary..."
echo "=========================================="

cat > .dockge-setup-summary.txt << EOF
ShowWise Dockge Deployment Setup Summary
Generated: $(date)

SECURITY CONFIGURATION:
  Security Backend Secret: [CONFIGURED]
  Main App Secret: [CONFIGURED]
  Home App Secret: [CONFIGURED]
  Backend Secret: [CONFIGURED]

DATABASE CONFIGURATION:
  Security DB User: security_user
  Organization DB User: org_user
  WebApp DB User: webapp_user
  All passwords: [CONFIGURED IN .env]

API KEYS:
  API Integration Key: [CONFIGURED]
  API Integration Secret: [CONFIGURED]
  Admin API Key: [CONFIGURED]

CLOUDFLARE:
  Turnstile Site Key: $([ ! -z "$TURNSTILE_SITE" ] && echo "[CONFIGURED]" || echo "[NOT SET]")
  Turnstile Secret: $([ ! -z "$TURNSTILE_SECRET" ] && echo "[CONFIGURED]" || echo "[NOT SET]")

DISCORD (Optional):
  Bot Token: $([ ! -z "$DISCORD_TOKEN" ] && echo "[CONFIGURED]" || echo "[NOT CONFIGURED]")
  Guild ID: $([ ! -z "$DISCORD_GUILD" ] && echo "[CONFIGURED]" || echo "[NOT CONFIGURED]")

NEXT STEPS:
1. Review .env file
2. Start deployment with docker-compose
3. Monitor logs for any errors
4. Verify all services are healthy

For documentation, see: DOCKGE_DEPLOYMENT_GUIDE.md
EOF

echo -e "${GREEN}✓ Setup summary saved to .dockge-setup-summary.txt${NC}"
echo ""
echo -e "${GREEN}All setup steps completed successfully!${NC}"
