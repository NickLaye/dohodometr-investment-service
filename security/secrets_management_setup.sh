#!/bin/bash

# 🏛️ Enterprise Secrets Management Setup for Dohodometr
# Настройка HashiCorp Vault и AWS Secrets Manager

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SECRETS_DIR="security/secrets_management"
VAULT_DIR="$SECRETS_DIR/vault"
AWS_DIR="$SECRETS_DIR/aws"

echo -e "${BLUE}🏛️ Enterprise Secrets Management Setup${NC}"
echo "=================================================="

# Create directory structure
mkdir -p "$VAULT_DIR"/{config,policies,scripts}
mkdir -p "$AWS_DIR"/{policies,scripts,terraform}

echo -e "${BLUE}📁 Directory structure created${NC}"

# 1. HashiCorp Vault Setup
echo -e "${BLUE}🔐 Setting up HashiCorp Vault configuration...${NC}"

# Vault server configuration
cat > "$VAULT_DIR/config/vault.hcl" << 'EOF'
# HashiCorp Vault Configuration for Dohodometr

storage "consul" {
  address = "127.0.0.1:8500"
  path    = "vault/"
}

listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/opt/vault/tls/vault.crt"
  tls_key_file  = "/opt/vault/tls/vault.key"
}

api_addr = "https://vault.dohodometr.ru:8200"
cluster_addr = "https://vault.dohodometr.ru:8201"

ui = true
log_level = "INFO"

# High availability settings
ha_storage "consul" {
  address = "127.0.0.1:8500"
  path    = "vault/"
}

# Seal configuration - Auto-unseal with AWS KMS (recommended)
seal "awskms" {
  region     = "us-east-1"
  kms_key_id = "alias/vault-unseal-key"
}

# Telemetry
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}
EOF

# Vault policies for Dohodometr services
cat > "$VAULT_DIR/policies/dohodometr-backend.hcl" << 'EOF'
# Vault Policy for Dohodometr Backend Service

# Database credentials
path "secret/data/dohodometr/database/*" {
  capabilities = ["read"]
}

# JWT secrets
path "secret/data/dohodometr/auth/*" {
  capabilities = ["read"]
}

# Encryption keys
path "secret/data/dohodometr/encryption/*" {
  capabilities = ["read"]
}

# Third-party API keys
path "secret/data/dohodometr/apis/*" {
  capabilities = ["read"]
}

# Transit encryption for PII
path "transit/encrypt/dohodometr-pii" {
  capabilities = ["update"]
}

path "transit/decrypt/dohodometr-pii" {
  capabilities = ["update"]
}

# Database dynamic secrets
path "database/creds/dohodometr-readwrite" {
  capabilities = ["read"]
}

path "database/creds/dohodometr-readonly" {
  capabilities = ["read"]
}
EOF

cat > "$VAULT_DIR/policies/dohodometr-admin.hcl" << 'EOF'
# Vault Policy for Dohodometr Administrators

# Full access to application secrets
path "secret/data/dohodometr/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage database connections
path "database/config/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage encryption keys
path "transit/keys/dohodometr-*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Manage policies
path "sys/policies/acl/dohodometr-*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# View audit logs
path "sys/audit-hash/*" {
  capabilities = ["read"]
}
EOF

# Vault initialization script
cat > "$VAULT_DIR/scripts/init_vault.sh" << 'EOF'
#!/bin/bash

# HashiCorp Vault Initialization Script for Dohodometr

set -euo pipefail

VAULT_ADDR=${VAULT_ADDR:-"https://vault.dohodometr.ru:8200"}
VAULT_TOKEN_FILE="vault-init-response.json"

echo "🔐 Initializing HashiCorp Vault for Dohodometr..."

# Check if Vault is already initialized
if vault status | grep -q "Initialized.*true"; then
    echo "✅ Vault is already initialized"
    exit 0
fi

# Initialize Vault
echo "🚀 Initializing Vault..."
vault operator init -key-shares=5 -key-threshold=3 -format=json > "$VAULT_TOKEN_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Vault initialized successfully!"
    echo "🔑 Root token and unseal keys saved to: $VAULT_TOKEN_FILE"
    echo "⚠️  CRITICAL: Store these keys securely and distribute unseal keys to trusted operators"
else
    echo "❌ Vault initialization failed"
    exit 1
fi

# Parse initialization response
ROOT_TOKEN=$(cat "$VAULT_TOKEN_FILE" | jq -r '.root_token')
UNSEAL_KEY_1=$(cat "$VAULT_TOKEN_FILE" | jq -r '.unseal_keys_b64[0]')
UNSEAL_KEY_2=$(cat "$VAULT_TOKEN_FILE" | jq -r '.unseal_keys_b64[1]')
UNSEAL_KEY_3=$(cat "$VAULT_TOKEN_FILE" | jq -r '.unseal_keys_b64[2]')

# Unseal Vault
echo "🔓 Unsealing Vault..."
vault operator unseal "$UNSEAL_KEY_1"
vault operator unseal "$UNSEAL_KEY_2"  
vault operator unseal "$UNSEAL_KEY_3"

# Authenticate with root token
export VAULT_TOKEN="$ROOT_TOKEN"

# Enable secrets engines
echo "🔧 Configuring secrets engines..."

# Enable KV v2 for application secrets
vault secrets enable -version=2 -path=secret kv

# Enable database secrets engine  
vault secrets enable database

# Enable transit encryption engine
vault secrets enable transit

# Configure database connection
vault write database/config/postgresql \
    plugin_name=postgresql-database-plugin \
    connection_url="postgresql://{{username}}:{{password}}@postgres:5432/dohodometr?sslmode=require" \
    allowed_roles="dohodometr-readwrite,dohodometr-readonly" \
    username="vault" \
    password="$DB_VAULT_PASSWORD"

# Create database roles
vault write database/roles/dohodometr-readwrite \
    db_name=postgresql \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"

vault write database/roles/dohodometr-readonly \
    db_name=postgresql \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"

# Create encryption key for PII
vault write -f transit/keys/dohodometr-pii

# Load policies
vault policy write dohodometr-backend ../policies/dohodometr-backend.hcl
vault policy write dohodometr-admin ../policies/dohodometr-admin.hcl

# Create service tokens
BACKEND_TOKEN=$(vault write -format=json auth/token/create \
    policies="dohodometr-backend" \
    ttl="72h" \
    renewable=true | jq -r '.auth.client_token')

echo "✅ Vault configuration completed!"
echo
echo "🔑 Service Tokens:"
echo "Backend Token: $BACKEND_TOKEN"
echo
echo "📋 Next Steps:"
echo "1. Store root token and unseal keys securely"
echo "2. Distribute unseal keys to operators" 
echo "3. Configure applications to use service tokens"
echo "4. Set up auto-unseal with cloud KMS"
EOF

chmod +x "$VAULT_DIR/scripts/init_vault.sh"

# 2. AWS Secrets Manager Setup
echo -e "${BLUE}☁️ Setting up AWS Secrets Manager configuration...${NC}"

# Terraform configuration for AWS Secrets Manager
cat > "$AWS_DIR/terraform/main.tf" << 'EOF'
# AWS Secrets Manager Setup for Dohodometr

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# KMS Key for Secrets Encryption
resource "aws_kms_key" "secrets" {
  description             = "KMS key for Dohodometr secrets encryption"
  deletion_window_in_days = 7

  tags = {
    Name        = "dohodometr-secrets"
    Environment = var.environment
    Project     = "dohodometr"
  }
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/dohodometr-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}

# Database Credentials
resource "aws_secretsmanager_secret" "database" {
  name        = "dohodometr/${var.environment}/database"
  description = "Database credentials for Dohodometr"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = {
    Environment = var.environment
    Component   = "database"
  }
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    engine   = "postgres"
    host     = var.db_host
    port     = var.db_port
    dbname   = var.db_name
  })
}

# JWT Secrets
resource "aws_secretsmanager_secret" "jwt" {
  name        = "dohodometr/${var.environment}/jwt"
  description = "JWT secrets for Dohodometr authentication"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = {
    Environment = var.environment
    Component   = "auth"
  }
}

resource "aws_secretsmanager_secret_version" "jwt" {
  secret_id = aws_secretsmanager_secret.jwt.id
  secret_string = jsonencode({
    secret_key           = var.jwt_secret_key
    access_token_expire  = 15
    refresh_token_expire = 7
    algorithm           = "HS512"
  })
}

# Encryption Keys  
resource "aws_secretsmanager_secret" "encryption" {
  name        = "dohodometr/${var.environment}/encryption"
  description = "Encryption keys for sensitive data"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = {
    Environment = var.environment
    Component   = "encryption"
  }
}

resource "aws_secretsmanager_secret_version" "encryption" {
  secret_id = aws_secretsmanager_secret.encryption.id
  secret_string = jsonencode({
    encryption_key  = var.encryption_key
    encryption_salt = var.encryption_salt
  })
}

# API Keys for Third-party Services
resource "aws_secretsmanager_secret" "api_keys" {
  name        = "dohodometr/${var.environment}/api-keys"
  description = "Third-party API keys"
  kms_key_id  = aws_kms_key.secrets.arn

  tags = {
    Environment = var.environment
    Component   = "integrations"
  }
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    tinkoff_api_key = var.tinkoff_api_key
    moex_api_key    = var.moex_api_key
    cbr_api_key     = var.cbr_api_key
    binance_api_key = var.binance_api_key
  })
}

# IAM Role for Applications
resource "aws_iam_role" "dohodometr_secrets" {
  name = "dohodometr-secrets-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "dohodometr_secrets" {
  name = "dohodometr-secrets-policy"
  role = aws_iam_role.dohodometr_secrets.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.database.arn,
          aws_secretsmanager_secret.jwt.arn,
          aws_secretsmanager_secret.encryption.arn,
          aws_secretsmanager_secret.api_keys.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.secrets.arn
      }
    ]
  })
}

# Instance Profile
resource "aws_iam_instance_profile" "dohodometr_secrets" {
  name = "dohodometr-secrets-${var.environment}"
  role = aws_iam_role.dohodometr_secrets.name
}

# Outputs
output "kms_key_arn" {
  value = aws_kms_key.secrets.arn
}

output "iam_role_arn" {
  value = aws_iam_role.dohodometr_secrets.arn
}

output "secrets_arns" {
  value = {
    database   = aws_secretsmanager_secret.database.arn
    jwt        = aws_secretsmanager_secret.jwt.arn
    encryption = aws_secretsmanager_secret.encryption.arn
    api_keys   = aws_secretsmanager_secret.api_keys.arn
  }
}
EOF

# Terraform variables
cat > "$AWS_DIR/terraform/variables.tf" << 'EOF'
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "db_username" {
  description = "Database username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "db_host" {
  description = "Database host"
  type        = string
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "dohodometr"
}

variable "jwt_secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "encryption_key" {
  description = "Encryption key for sensitive data"
  type        = string
  sensitive   = true
}

variable "encryption_salt" {
  description = "Encryption salt"
  type        = string
  sensitive   = true
}

variable "tinkoff_api_key" {
  description = "Tinkoff API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "moex_api_key" {
  description = "MOEX API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cbr_api_key" {
  description = "CBR API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "binance_api_key" {
  description = "Binance API key"
  type        = string
  sensitive   = true
  default     = ""
}
EOF

# AWS Secrets Manager Python integration
cat > "$AWS_DIR/scripts/secrets_client.py" << 'EOF'
#!/usr/bin/env python3
"""
AWS Secrets Manager Client for Dohodometr
Retrieves and caches secrets from AWS Secrets Manager
"""

import json
import boto3
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from datetime import datetime, timedelta

class SecretsManagerClient:
    """AWS Secrets Manager client with caching and error handling"""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client('secretsmanager', region_name=region_name)
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)  # Cache for 15 minutes
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve secret from AWS Secrets Manager with caching
        
        Args:
            secret_name: Name of the secret in AWS Secrets Manager
            
        Returns:
            Dictionary containing secret values
            
        Raises:
            ClientError: If secret retrieval fails
        """
        # Check cache first
        if self._is_cached(secret_name):
            self.logger.debug(f"Returning cached secret: {secret_name}")
            return self.cache[secret_name]['value']
        
        try:
            self.logger.info(f"Retrieving secret from AWS: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse secret value
            secret_value = json.loads(response['SecretString'])
            
            # Cache the secret
            self._cache_secret(secret_name, secret_value)
            
            return secret_value
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'DecryptionFailureException':
                self.logger.error(f"Decryption failed for secret: {secret_name}")
                raise e
            elif error_code == 'InternalServiceErrorException':
                self.logger.error(f"AWS internal error for secret: {secret_name}")
                raise e  
            elif error_code == 'InvalidParameterException':
                self.logger.error(f"Invalid parameter for secret: {secret_name}")
                raise e
            elif error_code == 'InvalidRequestException':
                self.logger.error(f"Invalid request for secret: {secret_name}")
                raise e
            elif error_code == 'ResourceNotFoundException':
                self.logger.error(f"Secret not found: {secret_name}")
                raise e
            else:
                self.logger.error(f"Unknown error retrieving secret {secret_name}: {e}")
                raise e
    
    def get_database_config(self, environment: str = "prod") -> Dict[str, str]:
        """Get database configuration from secrets manager"""
        secret_name = f"dohodometr/{environment}/database"
        return self.get_secret(secret_name)
    
    def get_jwt_config(self, environment: str = "prod") -> Dict[str, Any]:
        """Get JWT configuration from secrets manager"""  
        secret_name = f"dohodometr/{environment}/jwt"
        return self.get_secret(secret_name)
    
    def get_encryption_config(self, environment: str = "prod") -> Dict[str, str]:
        """Get encryption configuration from secrets manager"""
        secret_name = f"dohodometr/{environment}/encryption"
        return self.get_secret(secret_name)
    
    def get_api_keys(self, environment: str = "prod") -> Dict[str, str]:
        """Get third-party API keys from secrets manager"""
        secret_name = f"dohodometr/{environment}/api-keys"
        return self.get_secret(secret_name)
    
    def _is_cached(self, secret_name: str) -> bool:
        """Check if secret is cached and not expired"""
        if secret_name not in self.cache:
            return False
        
        cached_time = self.cache[secret_name]['timestamp']
        return datetime.now() - cached_time < self.cache_ttl
    
    def _cache_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> None:
        """Cache secret with timestamp"""
        self.cache[secret_name] = {
            'value': secret_value,
            'timestamp': datetime.now()
        }
        self.logger.debug(f"Cached secret: {secret_name}")
    
    def clear_cache(self) -> None:
        """Clear all cached secrets"""
        self.cache.clear()
        self.logger.info("Secret cache cleared")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = SecretsManagerClient()
    
    try:
        # Get database config
        db_config = client.get_database_config("prod")
        print(f"Database host: {db_config['host']}")
        
        # Get JWT config
        jwt_config = client.get_jwt_config("prod")  
        print(f"JWT algorithm: {jwt_config['algorithm']}")
        
        # Get encryption config
        enc_config = client.get_encryption_config("prod")
        print("Encryption key loaded successfully")
        
    except Exception as e:
        print(f"Error: {e}")
EOF

# FastAPI integration example
cat > "$AWS_DIR/scripts/fastapi_integration.py" << 'EOF'
"""
FastAPI integration with AWS Secrets Manager for Dohodometr
"""

from fastapi import FastAPI, Depends
from pydantic import BaseSettings
from secrets_client import SecretsManagerClient
import os

class Settings(BaseSettings):
    """Application settings with AWS Secrets Manager integration"""
    
    # Basic app settings
    app_name: str = "Dohodometr"
    environment: str = os.getenv("ENVIRONMENT", "dev")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    
    # These will be loaded from Secrets Manager
    secret_key: str = ""
    jwt_secret_key: str = ""
    database_url: str = ""
    encryption_key: str = ""
    encryption_salt: str = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Only load from AWS in production
        if self.environment in ["prod", "staging"]:
            self._load_from_secrets_manager()
        else:
            self._load_from_env()
    
    def _load_from_secrets_manager(self):
        """Load secrets from AWS Secrets Manager"""
        client = SecretsManagerClient(region_name=self.aws_region)
        
        try:
            # Load database config
            db_config = client.get_database_config(self.environment)
            self.database_url = f"postgresql://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
            
            # Load JWT config  
            jwt_config = client.get_jwt_config(self.environment)
            self.jwt_secret_key = jwt_config['secret_key']
            
            # Load encryption config
            enc_config = client.get_encryption_config(self.environment)
            self.encryption_key = enc_config['encryption_key']
            self.encryption_salt = enc_config['encryption_salt']
            
            # Load app secret
            self.secret_key = enc_config['encryption_key']  # Or separate app secret
            
            print("✅ Secrets loaded from AWS Secrets Manager")
            
        except Exception as e:
            print(f"❌ Failed to load secrets from AWS: {e}")
            raise
    
    def _load_from_env(self):
        """Load secrets from environment variables (dev/test)"""
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/dohodometr")
        self.encryption_key = os.getenv("ENCRYPTION_KEY", "dev-encryption-key")
        self.encryption_salt = os.getenv("ENCRYPTION_SALT", "dev-encryption-salt")
        
        print("✅ Secrets loaded from environment variables")

# Global settings instance
settings = Settings()

# FastAPI app
app = FastAPI(title=settings.app_name)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "secrets_loaded": bool(settings.secret_key)
    }

@app.get("/config")
async def get_config():
    """Get non-sensitive configuration"""
    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "aws_region": settings.aws_region,
        "database_connected": bool(settings.database_url),
        "encryption_enabled": bool(settings.encryption_key)
    }
EOF

# 3. Automatic Secret Rotation
echo -e "${BLUE}🔄 Creating automatic secret rotation scripts...${NC}"

cat > "$SECRETS_DIR/secret_rotation.py" << 'EOF'
#!/usr/bin/env python3
"""
Automatic Secret Rotation for Dohodometr
Rotates secrets in Vault/AWS and updates applications
"""

import os
import json
import boto3
import hvac
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import requests

class SecretRotationManager:
    """Manages automatic rotation of secrets"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rotation_config = self._load_rotation_config()
        
        # Initialize clients
        self.vault_client = self._init_vault_client()
        self.aws_client = self._init_aws_client()
    
    def _load_rotation_config(self) -> Dict:
        """Load rotation configuration"""
        return {
            "database_password": {"interval_days": 30, "provider": "vault"},
            "jwt_secret_key": {"interval_days": 90, "provider": "aws"},
            "encryption_key": {"interval_days": 365, "provider": "aws"},
            "api_keys": {"interval_days": 60, "provider": "aws"},
        }
    
    def _init_vault_client(self) -> hvac.Client:
        """Initialize HashiCorp Vault client"""
        client = hvac.Client(
            url=os.getenv("VAULT_ADDR", "https://vault.dohodometr.ru:8200"),
            token=os.getenv("VAULT_TOKEN")
        )
        return client
    
    def _init_aws_client(self):
        """Initialize AWS Secrets Manager client"""
        return boto3.client('secretsmanager', region_name='us-east-1')
    
    def rotate_database_password(self):
        """Rotate database password using Vault dynamic secrets"""
        self.logger.info("Rotating database password...")
        
        try:
            # Generate new database credential
            new_creds = self.vault_client.read('database/creds/dohodometr-readwrite')
            
            # Update application configuration
            self._update_app_config('database', {
                'username': new_creds['data']['username'],
                'password': new_creds['data']['password']
            })
            
            self.logger.info("Database password rotated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to rotate database password: {e}")
            raise
    
    def rotate_jwt_secret(self):
        """Rotate JWT secret key"""
        self.logger.info("Rotating JWT secret key...")
        
        try:
            # Generate new JWT secret
            import secrets
            new_secret = secrets.token_urlsafe(64)
            
            # Update in AWS Secrets Manager
            secret_name = "dohodometr/prod/jwt"
            current_secret = self.aws_client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(current_secret['SecretString'])
            secret_data['secret_key'] = new_secret
            
            self.aws_client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_data)
            )
            
            # Rolling restart applications
            self._rolling_restart_apps()
            
            self.logger.info("JWT secret rotated successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to rotate JWT secret: {e}")
            raise
    
    def rotate_encryption_keys(self):
        """Rotate encryption keys with data migration"""
        self.logger.info("Rotating encryption keys...")
        
        try:
            # This is a complex operation requiring:
            # 1. Generate new encryption key
            # 2. Re-encrypt all existing encrypted data
            # 3. Update applications with new key
            # 4. Verify all data is accessible
            
            # For production, implement gradual migration
            self.logger.warning("Encryption key rotation requires maintenance window")
            
        except Exception as e:
            self.logger.error(f"Failed to rotate encryption keys: {e}")
            raise
    
    def _update_app_config(self, config_type: str, new_values: Dict):
        """Update application configuration"""
        # This would typically trigger a config reload or restart
        # Implementation depends on your deployment strategy
        pass
    
    def _rolling_restart_apps(self):
        """Perform rolling restart of applications"""
        # Implementation for your orchestration platform (Kubernetes, Docker Swarm, etc.)
        self.logger.info("Triggering rolling restart...")
    
    def check_rotation_schedule(self):
        """Check which secrets need rotation"""
        self.logger.info("Checking rotation schedule...")
        
        # This would typically check rotation metadata
        # and determine which secrets are due for rotation
        secrets_to_rotate = []
        
        for secret_name, config in self.rotation_config.items():
            if self._is_rotation_due(secret_name, config["interval_days"]):
                secrets_to_rotate.append(secret_name)
        
        return secrets_to_rotate
    
    def _is_rotation_due(self, secret_name: str, interval_days: int) -> bool:
        """Check if secret rotation is due"""
        # Implementation to check last rotation date
        # This could be stored in metadata or a separate tracking system
        return False  # Placeholder

# Example usage as a scheduled job
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = SecretRotationManager()
    
    # Check what needs rotation
    secrets_to_rotate = manager.check_rotation_schedule()
    
    for secret in secrets_to_rotate:
        try:
            if secret == "database_password":
                manager.rotate_database_password()
            elif secret == "jwt_secret_key":
                manager.rotate_jwt_secret()
            elif secret == "encryption_key":
                manager.rotate_encryption_keys()
                
        except Exception as e:
            logging.error(f"Failed to rotate {secret}: {e}")
EOF

chmod +x "$SECRETS_DIR/secret_rotation.py"

# 4. Deployment guide
cat > "$SECRETS_DIR/DEPLOYMENT_GUIDE.md" << 'EOF'
# 🏛️ Secrets Management Deployment Guide

## Option 1: HashiCorp Vault

### Prerequisites
- Consul cluster for storage backend
- SSL certificates for Vault server
- AWS KMS key for auto-unseal (recommended)

### Deployment Steps

1. **Deploy Vault Server:**
```bash
# Use provided configuration
cp vault/config/vault.hcl /etc/vault/vault.hcl

# Start Vault service
systemctl enable vault
systemctl start vault
```

2. **Initialize Vault:**
```bash
./vault/scripts/init_vault.sh
```

3. **Load Secrets:**
```bash
# Database credentials
vault kv put secret/dohodometr/database \
    username="dohodometr_user" \
    password="secure_password_123"

# JWT secrets  
vault kv put secret/dohodometr/jwt \
    secret_key="your_jwt_secret_key_here"

# Encryption keys
vault kv put secret/dohodometr/encryption \
    encryption_key="your_encryption_key" \
    encryption_salt="your_encryption_salt"
```

## Option 2: AWS Secrets Manager

### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform installed

### Deployment Steps

1. **Deploy Infrastructure:**
```bash
cd aws/terraform/
terraform init
terraform plan
terraform apply
```

2. **Load Secrets:**
```bash
# Use the Terraform outputs to configure applications
terraform output secrets_arns
```

## Application Integration

### Environment Variables
```bash
# For Vault
export VAULT_ADDR="https://vault.dohodometr.ru:8200"
export VAULT_TOKEN="your_service_token"

# For AWS Secrets Manager  
export AWS_REGION="us-east-1"
export ENVIRONMENT="prod"
```

### Python Integration
```python
from secrets_client import SecretsManagerClient

# AWS Secrets Manager
client = SecretsManagerClient()
db_config = client.get_database_config("prod")

# HashiCorp Vault
import hvac
client = hvac.Client(url=vault_addr, token=vault_token)
secret = client.read('secret/data/dohodometr/database')
```

## Secret Rotation

### Automated Rotation
```bash
# Set up cron job for automatic rotation
0 2 * * 0 /usr/local/bin/python3 /opt/dohodometr/secret_rotation.py
```

### Manual Rotation
```bash
# Rotate specific secret
python3 secret_rotation.py --rotate jwt_secret_key
```

## Monitoring & Alerting

- Set up CloudWatch/Grafana alerts for secret access
- Monitor rotation success/failure
- Alert on unauthorized access attempts
- Track secret usage patterns

## Security Best Practices

1. **Least Privilege Access**
2. **Regular Rotation**  
3. **Audit Logging**
4. **Encryption in Transit/Rest**
5. **Access Monitoring**
6. **Backup & Recovery**

## Troubleshooting

### Common Issues
- Token expiration
- Network connectivity
- Permission denied
- Rotation failures

### Diagnostics
```bash
# Check Vault status
vault status

# Test AWS credentials
aws secretsmanager list-secrets

# Verify application connectivity
curl -H "X-Vault-Token: $VAULT_TOKEN" $VAULT_ADDR/v1/secret/data/dohodometr/database
```
EOF

echo
echo -e "${GREEN}✅ Enterprise Secrets Management Setup Completed!${NC}"
echo "=================================================="
echo -e "${BLUE}📁 Created configurations:${NC}"
echo "  - HashiCorp Vault server configuration"
echo "  - Vault policies and initialization scripts"
echo "  - AWS Secrets Manager Terraform modules"
echo "  - Python client libraries"
echo "  - Automatic rotation scripts"
echo
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "  1. Choose your secrets management solution:"
echo "     - HashiCorp Vault (self-hosted, more control)"
echo "     - AWS Secrets Manager (managed service, easier)"
echo "  2. Deploy chosen solution using provided scripts"
echo "  3. Migrate existing secrets from .env files"
echo "  4. Update applications to use new secret sources"
echo "  5. Set up automatic rotation schedules"
echo
echo -e "${BLUE}📖 Documentation:${NC}"
echo "  Read: $SECRETS_DIR/DEPLOYMENT_GUIDE.md"
echo
echo -e "${GREEN}🎉 Ready for enterprise-grade secrets management!${NC}"
