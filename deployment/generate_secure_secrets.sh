#!/bin/bash

# 🔐 Secure Secrets Generator for Dohodometr Production
# This script generates cryptographically secure secrets for production deployment
# 
# Usage: ./generate_secure_secrets.sh [output-file]
# Example: ./generate_secure_secrets.sh .env.production

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default output file
OUTPUT_FILE="${1:-.env.production}"

echo -e "${BLUE}🔐 Dohodometr Secure Secrets Generator${NC}"
echo "=================================================="

# Function to generate secure password
generate_secure_password() {
    local length=${1:-32}
    openssl rand -base64 $((length * 3 / 4)) | tr -d "=+/" | cut -c1-${length}
}

# Function to generate hex key
generate_hex_key() {
    local length=${1:-32}
    openssl rand -hex ${length}
}

# Function to validate password strength
validate_password_strength() {
    local password="$1"
    local min_length=16
    
    if [ ${#password} -lt $min_length ]; then
        echo -e "${RED}❌ Password too short (minimum $min_length characters)${NC}"
        return 1
    fi
    
    # Check for complexity (at least 3 character types)
    local complexity=0
    if [[ "$password" =~ [a-z] ]]; then ((complexity++)); fi
    if [[ "$password" =~ [A-Z] ]]; then ((complexity++)); fi
    if [[ "$password" =~ [0-9] ]]; then ((complexity++)); fi
    if [[ "$password" =~ [^a-zA-Z0-9] ]]; then ((complexity++)); fi
    
    if [ $complexity -lt 3 ]; then
        echo -e "${RED}❌ Password lacks complexity${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Password meets security requirements${NC}"
    return 0
}

# Check if output file exists
if [ -f "$OUTPUT_FILE" ]; then
    echo -e "${YELLOW}⚠️  File $OUTPUT_FILE already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Aborted${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}🔄 Generating secure secrets...${NC}"

# Generate core application secrets
SECRET_KEY=$(generate_secure_password 64)
JWT_SECRET_KEY=$(generate_secure_password 64)
ENCRYPTION_KEY=$(generate_hex_key 32)
ENCRYPTION_SALT=$(generate_hex_key 32)

# Generate database credentials
POSTGRES_PASSWORD=$(generate_secure_password 32)
REDIS_PASSWORD=$(generate_secure_password 24)

# Generate MinIO credentials
MINIO_ACCESS_KEY=$(generate_secure_password 20)
MINIO_SECRET_KEY=$(generate_secure_password 40)

# Generate additional secure values
SESSION_SECRET=$(generate_secure_password 32)
CSRF_SECRET=$(generate_secure_password 32)

# Validate generated passwords
echo -e "${BLUE}🔍 Validating password strength...${NC}"
validate_password_strength "$SECRET_KEY"
validate_password_strength "$JWT_SECRET_KEY"
validate_password_strength "$POSTGRES_PASSWORD"

# Create the .env file
cat > "$OUTPUT_FILE" << EOF
# =================================
# DOHODOMETR PRODUCTION SECRETS
# =================================
# Generated on: $(date)
# 
# ⚠️  CRITICAL SECURITY NOTICE:
# - Keep this file secure and never commit to version control
# - Use a secret manager in production (HashiCorp Vault, AWS Secrets Manager, etc.)
# - Rotate secrets regularly (every 90 days minimum)
# - Monitor access to this file
# =================================

# Core Application Secrets
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
ENCRYPTION_SALT=${ENCRYPTION_SALT}
SESSION_SECRET=${SESSION_SECRET}
CSRF_SECRET=${CSRF_SECRET}

# JWT Configuration
JWT_ALGORITHM=HS512
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Credentials
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/dohodometr

# Redis Credentials
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# MinIO/S3 Credentials
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY}

# Security Configuration
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://dohodometr.ru,https://www.dohodometr.ru
TRUSTED_HOSTS=dohodometr.ru,www.dohodometr.ru

# Rate Limiting (Stricter for production)
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
RATE_LIMIT_PER_DAY=5000
MAX_LOGIN_ATTEMPTS=3
LOGIN_ATTEMPT_RESET_TIME=1800

# Password Policy
PASSWORD_MIN_LENGTH=12
ARGON2_MEMORY_COST=131072
ARGON2_TIME_COST=4
ARGON2_PARALLELISM=2

# Session Configuration
SESSION_LIFETIME_HOURS=24
REMEMBER_ME_DURATION_DAYS=30

# SSL/TLS Configuration
FORCE_HTTPS=true
SECURE_COOKIES=true
SECURE_HEADERS=true

# Monitoring & Logging
LOG_LEVEL=INFO
SENTRY_DSN=# Add your Sentry DSN here
PROMETHEUS_ENABLED=true

# Backup Configuration
BACKUP_ENCRYPTION_KEY=$(generate_hex_key 32)
BACKUP_RETENTION_DAYS=90

# =================================
# GENERATED HASHES FOR VERIFICATION
# =================================
# SECRET_KEY_SHA256=$(echo -n "$SECRET_KEY" | sha256sum | cut -d' ' -f1)
# JWT_SECRET_SHA256=$(echo -n "$JWT_SECRET_KEY" | sha256sum | cut -d' ' -f1)
# Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

# Set secure permissions
chmod 600 "$OUTPUT_FILE"

# Display summary
echo
echo -e "${GREEN}✅ Secure secrets generated successfully!${NC}"
echo "=================================================="
echo -e "📁 Output file: ${BLUE}$OUTPUT_FILE${NC}"
echo -e "🔒 File permissions: ${GREEN}600 (owner read/write only)${NC}"
echo
echo -e "${YELLOW}🛡️  SECURITY CHECKLIST:${NC}"
echo "  □ Store this file in a secure location"
echo "  □ Never commit this file to version control" 
echo "  □ Use a secret manager in production"
echo "  □ Set up secret rotation (every 90 days)"
echo "  □ Monitor access to secrets"
echo "  □ Configure backup encryption"
echo "  □ Test secrets in staging environment first"
echo
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "  1. Copy this file to your production server"
echo "  2. Update your docker-compose or deployment configuration"
echo "  3. Restart all services to pick up new secrets"
echo "  4. Test authentication and database connectivity"
echo "  5. Set up monitoring for secret usage"
echo
echo -e "${RED}⚠️  IMPORTANT REMINDERS:${NC}"
echo "  • Change default secrets immediately in production"
echo "  • Use environment-specific secrets (dev/staging/prod)"
echo "  • Enable audit logging for secret access"
echo "  • Have an incident response plan for secret compromise"
echo
echo -e "${GREEN}🎉 Ready for secure production deployment!${NC}"
EOF
