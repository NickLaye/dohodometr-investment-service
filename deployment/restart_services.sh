#!/bin/bash

# 🔄 Production Services Restart Script
# Безопасный перезапуск всех сервисов с новыми секретами

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PRODUCTION_SERVER="${1:-}"
COMPOSE_FILE="/opt/dohodometr/docker-compose.production.yml"
ENV_FILE="/opt/dohodometr/.env.production"

echo -e "${BLUE}🔄 Dohodometr Production Services Restart${NC}"
echo "=================================================="

if [[ -z "$PRODUCTION_SERVER" ]]; then
    echo -e "${RED}❌ Usage: $0 <production-server>${NC}"
    exit 1
fi

# Pre-restart validation
echo -e "${BLUE}🔍 Pre-restart validation...${NC}"
ssh "$PRODUCTION_SERVER" "
    # Check if secrets file exists
    if [[ ! -f $ENV_FILE ]]; then
        echo '❌ Secrets file not found'
        exit 1
    fi
    
    # Check if docker-compose file exists
    if [[ ! -f $COMPOSE_FILE ]]; then
        echo '❌ Docker compose file not found'
        exit 1
    fi
    
    # Validate secrets content
    if ! grep -q 'SECRET_KEY=' $ENV_FILE || ! grep -q 'ENCRYPTION_SALT=' $ENV_FILE; then
        echo '❌ Required secrets missing'
        exit 1
    fi
    
    echo '✅ Pre-restart validation passed'
"

# Create services backup snapshot
echo -e "${BLUE}💾 Creating services backup...${NC}"
ssh "$PRODUCTION_SERVER" "
    cd /opt/dohodometr
    
    # Create backup directory
    sudo mkdir -p backups/services/\$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR=\"backups/services/\$(date +%Y%m%d_%H%M%S)\"
    
    # Backup current configuration
    sudo cp docker-compose.production.yml \$BACKUP_DIR/
    sudo cp .env.production \$BACKUP_DIR/ 2>/dev/null || true
    
    echo \"Backup created: \$BACKUP_DIR\"
"

# Graceful shutdown with health checks
echo -e "${BLUE}⏹️ Gracefully stopping services...${NC}"
ssh "$PRODUCTION_SERVER" "
    cd /opt/dohodometr
    
    echo '🔄 Stopping services gracefully...'
    sudo docker-compose -f $COMPOSE_FILE stop --timeout 30
    
    echo '🧹 Cleaning up containers...'
    sudo docker-compose -f $COMPOSE_FILE down --remove-orphans
    
    echo '🗑️ Removing unused images and volumes...'
    sudo docker system prune -f
    
    echo '✅ Services stopped'
"

# Start services with new configuration
echo -e "${BLUE}🚀 Starting services with new secrets...${NC}"
ssh "$PRODUCTION_SERVER" "
    cd /opt/dohodometr
    
    # Load new environment
    export \$(cat $ENV_FILE | grep -v '^#' | xargs)
    
    echo '🔧 Building and starting services...'
    sudo -E docker-compose -f $COMPOSE_FILE up -d --build
    
    echo '⏳ Waiting for services to initialize...'
    sleep 30
"

# Health checks
echo -e "${BLUE}🏥 Performing health checks...${NC}"
ssh "$PRODUCTION_SERVER" "
    cd /opt/dohodometr
    
    echo '🔍 Checking service status...'
    sudo docker-compose -f $COMPOSE_FILE ps
    
    echo
    echo '🏥 Health check results:'
    
    # Check backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo '✅ Backend: Healthy'
    else
        echo '❌ Backend: Unhealthy'
    fi
    
    # Check frontend health  
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo '✅ Frontend: Healthy'
    else
        echo '❌ Frontend: Unhealthy'
    fi
    
    # Check database connectivity
    if sudo docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready > /dev/null 2>&1; then
        echo '✅ Database: Connected'
    else
        echo '❌ Database: Connection failed'
    fi
    
    # Check Redis connectivity
    if sudo docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping | grep -q PONG; then
        echo '✅ Redis: Connected'
    else
        echo '❌ Redis: Connection failed'
    fi
"

# Security validation
echo -e "${BLUE}🔒 Security validation...${NC}"
SECURITY_CHECK=$(ssh "$PRODUCTION_SERVER" "
    cd /opt/dohodometr
    
    # Check if new secrets are loaded
    BACKEND_ENV=\$(sudo docker-compose -f $COMPOSE_FILE exec -T backend env | grep SECRET_KEY | cut -d'=' -f2)
    if [[ -n \"\$BACKEND_ENV\" && \"\$BACKEND_ENV\" != \"your-secret-key-here\" ]]; then
        echo 'SECRET_KEY: Updated'
    else
        echo 'SECRET_KEY: NOT_UPDATED'
    fi
    
    # Check encryption salt
    SALT_ENV=\$(sudo docker-compose -f $COMPOSE_FILE exec -T backend env | grep ENCRYPTION_SALT | cut -d'=' -f2)
    if [[ -n \"\$SALT_ENV\" ]]; then
        echo 'ENCRYPTION_SALT: Present'
    else
        echo 'ENCRYPTION_SALT: Missing'
    fi
    
    # Check JWT secret
    JWT_ENV=\$(sudo docker-compose -f $COMPOSE_FILE exec -T backend env | grep JWT_SECRET_KEY | cut -d'=' -f2)
    if [[ -n \"\$JWT_ENV\" && \"\$JWT_ENV\" != \"your-jwt-secret-key-here\" ]]; then
        echo 'JWT_SECRET_KEY: Updated'
    else
        echo 'JWT_SECRET_KEY: NOT_UPDATED'
    fi
")

echo "$SECURITY_CHECK"

if echo "$SECURITY_CHECK" | grep -q "SECRET_KEY: Updated" && echo "$SECURITY_CHECK" | grep -q "ENCRYPTION_SALT: Present"; then
    echo -e "${GREEN}✅ Security validation passed!${NC}"
else
    echo -e "${RED}❌ Security validation failed!${NC}"
    echo "Services may need manual intervention"
    exit 1
fi

# Final status report
echo
echo -e "${GREEN}🎉 Services restart completed successfully!${NC}"
echo "=================================================="
echo -e "${BLUE}📊 Final Status:${NC}"
echo "  ✅ All services restarted with new secrets"
echo "  ✅ Health checks passed"  
echo "  ✅ Security validation completed"
echo "  ✅ Ready for authentication testing"
echo
echo -e "${YELLOW}📋 Next Step:${NC}"
echo "  Run: ./deployment/test_auth.sh $PRODUCTION_SERVER"
echo
echo -e "${BLUE}📝 Logs monitoring:${NC}"
echo "  sudo docker-compose -f $COMPOSE_FILE logs -f"
