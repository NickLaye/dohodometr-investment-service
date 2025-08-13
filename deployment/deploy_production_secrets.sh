#!/bin/bash

# 🔐 Production Secrets Deployment Script
# Безопасный перенос секретов на production сервер

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_SERVER="${1:-}"
SECRETS_FILE=".env.production.example"
REMOTE_PATH="/opt/dohodometr/.env.production"
BACKUP_PATH="/opt/dohodometr/backups/.env.backup.$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}🚀 Dohodometr Production Secrets Deployment${NC}"
echo "=================================================="

# Validate inputs
if [[ -z "$PRODUCTION_SERVER" ]]; then
    echo -e "${RED}❌ Usage: $0 <production-server>${NC}"
    echo "Example: $0 user@dohodometr-prod.example.com"
    exit 1
fi

if [[ ! -f "$SECRETS_FILE" ]]; then
    echo -e "${RED}❌ Secrets file not found: $SECRETS_FILE${NC}"
    echo "Run: ./deployment/generate_secure_secrets.sh first"
    exit 1
fi

# Test SSH connection
echo -e "${BLUE}🔍 Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=10 "$PRODUCTION_SERVER" "echo 'SSH connection successful'" > /dev/null 2>&1; then
    echo -e "${RED}❌ Cannot connect to $PRODUCTION_SERVER${NC}"
    echo "Please check SSH configuration and server availability"
    exit 1
fi

echo -e "${GREEN}✅ SSH connection successful${NC}"

# Create backup of existing .env if exists
echo -e "${BLUE}💾 Creating backup of existing secrets...${NC}"
ssh "$PRODUCTION_SERVER" "
    sudo mkdir -p /opt/dohodometr/backups
    if [[ -f $REMOTE_PATH ]]; then
        sudo cp $REMOTE_PATH $BACKUP_PATH
        echo 'Backup created: $BACKUP_PATH'
    else
        echo 'No existing secrets file found'
    fi
"

# Transfer secrets file with secure permissions
echo -e "${BLUE}📤 Transferring new secrets...${NC}"
scp "$SECRETS_FILE" "$PRODUCTION_SERVER:/tmp/.env.production.new"

# Move to final location with correct permissions
ssh "$PRODUCTION_SERVER" "
    sudo mkdir -p /opt/dohodometr
    sudo mv /tmp/.env.production.new $REMOTE_PATH
    sudo chown dohodometr:dohodometr $REMOTE_PATH
    sudo chmod 600 $REMOTE_PATH
    echo 'Secrets deployed successfully'
"

# Validate deployment
echo -e "${BLUE}🔍 Validating deployment...${NC}"
VALIDATION_RESULT=$(ssh "$PRODUCTION_SERVER" "
    if [[ -f $REMOTE_PATH ]]; then
        PERMS=\$(stat -c '%a' $REMOTE_PATH)
        OWNER=\$(stat -c '%U:%G' $REMOTE_PATH)
        SIZE=\$(stat -c '%s' $REMOTE_PATH)
        echo \"File exists: YES\"
        echo \"Permissions: \$PERMS\"
        echo \"Owner: \$OWNER\"
        echo \"Size: \$SIZE bytes\"
        
        # Check for required secrets
        if grep -q 'SECRET_KEY=' $REMOTE_PATH && grep -q 'ENCRYPTION_SALT=' $REMOTE_PATH; then
            echo \"Required secrets: PRESENT\"
        else
            echo \"Required secrets: MISSING\"
        fi
    else
        echo \"File exists: NO\"
    fi
")

echo "$VALIDATION_RESULT"

if echo "$VALIDATION_RESULT" | grep -q "File exists: YES" && echo "$VALIDATION_RESULT" | grep -q "Required secrets: PRESENT"; then
    echo -e "${GREEN}✅ Secrets deployment successful!${NC}"
    echo
    echo -e "${YELLOW}🔒 SECURITY REMINDER:${NC}"
    echo "  • Secrets are now deployed with 600 permissions"
    echo "  • Backup created at: $BACKUP_PATH"
    echo "  • Ready for service restart"
else
    echo -e "${RED}❌ Deployment validation failed!${NC}"
    exit 1
fi

echo
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "  1. Restart all services: ./deployment/restart_services.sh $PRODUCTION_SERVER"
echo "  2. Test authentication: ./deployment/test_auth.sh $PRODUCTION_SERVER"
echo "  3. Monitor logs for any issues"
echo
echo -e "${GREEN}🎉 Ready for service restart!${NC}"
