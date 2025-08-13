#!/bin/bash

# 🔍 Internal Security Audit for Dohodometr
# Комплексный внутренний аудит безопасности

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

AUDIT_DIR="security/internal_audit"
REPORT_DIR="$AUDIT_DIR/reports/$(date +%Y%m%d_%H%M%S)"
TEMPLATES_DIR="$AUDIT_DIR/templates"

echo -e "${BLUE}🔍 Dohodometr Internal Security Audit${NC}"
echo "=================================================="

# Create directory structure
mkdir -p "$REPORT_DIR"/{code,infrastructure,compliance,penetration}
mkdir -p "$TEMPLATES_DIR"
mkdir -p "$AUDIT_DIR/scripts"

echo -e "${BLUE}📁 Audit directories created${NC}"

# 1. Code Security Audit Checklist
echo -e "${BLUE}📋 Creating code security audit checklist...${NC}"
cat > "$TEMPLATES_DIR/code_security_checklist.md" << 'EOF'
# 📋 Code Security Audit Checklist - Dohodometr

**Auditor:** ________________  
**Date:** ________________  
**Component:** ________________

## 🔒 Authentication & Authorization

### JWT Implementation
- [ ] JWT tokens have appropriate expiration times (access: 15min, refresh: 7 days)
- [ ] JWT algorithm is fixed and secure (HS512)
- [ ] JTI (JWT ID) is used for token revocation
- [ ] Token blacklist is implemented and checked
- [ ] Refresh token rotation is implemented

### Password Security
- [ ] Passwords are hashed with Argon2 or bcrypt
- [ ] Salt is unique per password (not hardcoded)
- [ ] Password strength requirements enforced (12+ chars, complexity)
- [ ] Password reset mechanism is secure
- [ ] Account lockout after failed attempts

### 2FA Implementation
- [ ] TOTP implementation uses cryptographically secure secrets
- [ ] QR codes are generated securely
- [ ] 2FA bypass mechanisms are secure
- [ ] Recovery codes are properly implemented

## 🗄️ Data Protection

### Input Validation
- [ ] All user inputs are validated and sanitized
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection (output encoding)
- [ ] File upload restrictions and scanning
- [ ] Rate limiting on all public endpoints

### Encryption
- [ ] Sensitive data encrypted at rest (AES-256-GCM)
- [ ] Encryption keys managed securely (not hardcoded)
- [ ] HTTPS enforced everywhere (HSTS enabled)
- [ ] Database connections encrypted
- [ ] Unique salt for each encryption operation

### PII Handling (152-ФЗ Compliance)
- [ ] Personal data classification implemented
- [ ] Data minimization principles followed
- [ ] Consent management system in place
- [ ] Data retention policies implemented (7 years)
- [ ] Data subject rights (access, deletion) implemented

## 🌐 API Security

### Endpoint Security
- [ ] Authentication required on protected endpoints
- [ ] Authorization checks implemented (RBAC)
- [ ] Rate limiting configured appropriately
- [ ] CORS configured securely
- [ ] Security headers implemented

### Error Handling
- [ ] Error messages don't leak sensitive information
- [ ] Stack traces disabled in production
- [ ] Logging doesn't contain sensitive data
- [ ] Custom error pages for 4xx/5xx codes

## 🏗️ Infrastructure Security

### Container Security
- [ ] Non-root users in containers (appuser:1001)
- [ ] Minimal base images used
- [ ] No secrets in Dockerfiles
- [ ] Health checks implemented
- [ ] Resource limits configured

### Network Security
- [ ] Network segmentation implemented
- [ ] Firewall rules configured
- [ ] VPN access for administration
- [ ] SSL/TLS certificates valid and current

## 📊 Monitoring & Logging

### Security Monitoring
- [ ] Authentication events logged
- [ ] Failed login attempts monitored
- [ ] Suspicious activity alerts configured
- [ ] Log aggregation and analysis
- [ ] Incident response procedures documented

### Audit Trail
- [ ] All critical operations logged
- [ ] Logs stored securely with integrity protection
- [ ] Log retention policy implemented
- [ ] Access to logs controlled and monitored

## 🔧 Configuration Security

### Environment Configuration
- [ ] Production environment properly configured
- [ ] Debug mode disabled in production
- [ ] Default credentials changed
- [ ] Unnecessary services disabled
- [ ] Security patches current

### Secrets Management
- [ ] No secrets in code or configuration files
- [ ] Secrets managed in dedicated system (Vault/AWS)
- [ ] Secret rotation procedures implemented
- [ ] Access to secrets logged and monitored

## 🧪 Testing & Quality

### Security Testing
- [ ] Unit tests for security functions
- [ ] Integration tests for auth flows
- [ ] Automated security scans in CI/CD
- [ ] Regular penetration testing
- [ ] Dependency vulnerability scanning

## 📚 Documentation & Processes

### Security Documentation
- [ ] Security policies documented
- [ ] Incident response plan exists
- [ ] Security training materials current
- [ ] Code review security checklist used
- [ ] Threat model documented

---

## 📊 SCORING

**Critical Issues (25 points each):**
- Hardcoded secrets: ___/25
- SQL injection vulnerabilities: ___/25
- Authentication bypass: ___/25
- Unencrypted sensitive data: ___/25

**High Issues (10 points each):**
- Missing input validation: ___/10
- Insufficient logging: ___/10
- Weak password policy: ___/10
- Missing security headers: ___/10

**Medium Issues (5 points each):**
- Configuration issues: ___/5
- Documentation gaps: ___/5
- Monitoring gaps: ___/5

**TOTAL SCORE:** ___/150

**GRADE:**
- 135-150: A (Excellent)
- 120-134: B (Good) 
- 100-119: C (Acceptable)
- 80-99: D (Needs Improvement)
- <80: F (Critical Issues)

**RECOMMENDATIONS:**
_List specific actions needed to address findings_

**AUDITOR SIGNATURE:** ________________  
**DATE:** ________________
EOF

# 2. Infrastructure Security Audit Script
echo -e "${BLUE}🏗️ Creating infrastructure security audit script...${NC}"
cat > "$AUDIT_DIR/scripts/infrastructure_audit.sh" << 'EOF'
#!/bin/bash

# Infrastructure Security Audit Script

REPORT_FILE="$1"
if [[ -z "$REPORT_FILE" ]]; then
    REPORT_FILE="infrastructure_audit_$(date +%Y%m%d_%H%M%S).txt"
fi

echo "🏗️ INFRASTRUCTURE SECURITY AUDIT REPORT" > "$REPORT_FILE"
echo "Generated: $(date)" >> "$REPORT_FILE"
echo "===============================================" >> "$REPORT_FILE"
echo >> "$REPORT_FILE"

# 1. Docker Container Security
echo "🐳 DOCKER CONTAINER SECURITY" >> "$REPORT_FILE"
echo "-----------------------------" >> "$REPORT_FILE"

if command -v docker &> /dev/null; then
    echo "Docker version: $(docker --version)" >> "$REPORT_FILE"
    
    # Check for containers running as root
    echo >> "$REPORT_FILE"
    echo "Containers running as root:" >> "$REPORT_FILE"
    docker ps --format "table {{.Names}}\t{{.Image}}" | while read line; do
        if [[ "$line" != "NAMES"* ]]; then
            container_name=$(echo "$line" | awk '{print $1}')
            user=$(docker exec "$container_name" whoami 2>/dev/null || echo "N/A")
            echo "$container_name: $user" >> "$REPORT_FILE"
        fi
    done
    
    # Check for exposed ports
    echo >> "$REPORT_FILE"  
    echo "Exposed ports:" >> "$REPORT_FILE"
    docker ps --format "table {{.Names}}\t{{.Ports}}" >> "$REPORT_FILE"
    
else
    echo "Docker not installed or not accessible" >> "$REPORT_FILE"
fi

echo >> "$REPORT_FILE"

# 2. Network Security
echo "🌐 NETWORK SECURITY" >> "$REPORT_FILE"
echo "-------------------" >> "$REPORT_FILE"

# Check open ports
echo "Open network ports:" >> "$REPORT_FILE"
if command -v ss &> /dev/null; then
    ss -tuln >> "$REPORT_FILE"
elif command -v netstat &> /dev/null; then
    netstat -tuln >> "$REPORT_FILE"
else
    echo "No network monitoring tool available" >> "$REPORT_FILE"
fi

echo >> "$REPORT_FILE"

# Check firewall status
echo "Firewall status:" >> "$REPORT_FILE"
if command -v ufw &> /dev/null; then
    ufw status >> "$REPORT_FILE"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --state >> "$REPORT_FILE"
    firewall-cmd --list-all >> "$REPORT_FILE"
else
    echo "No firewall tool detected" >> "$REPORT_FILE"
fi

echo >> "$REPORT_FILE"

# 3. SSL/TLS Configuration
echo "🔒 SSL/TLS CONFIGURATION" >> "$REPORT_FILE"
echo "------------------------" >> "$REPORT_FILE"

# Check certificate validity
DOMAINS=("dohodometr.ru" "api.dohodometr.ru")
for domain in "${DOMAINS[@]}"; do
    echo "Checking $domain:" >> "$REPORT_FILE"
    if command -v openssl &> /dev/null; then
        echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | \
        openssl x509 -noout -dates 2>/dev/null >> "$REPORT_FILE" || \
        echo "Unable to connect to $domain" >> "$REPORT_FILE"
    else
        echo "OpenSSL not available" >> "$REPORT_FILE"
    fi
    echo >> "$REPORT_FILE"
done

# 4. System Security
echo "💻 SYSTEM SECURITY" >> "$REPORT_FILE"
echo "------------------" >> "$REPORT_FILE"

# Check system updates
echo "System update status:" >> "$REPORT_FILE"
if command -v apt &> /dev/null; then
    apt list --upgradable 2>/dev/null | head -10 >> "$REPORT_FILE"
elif command -v yum &> /dev/null; then
    yum check-update 2>/dev/null | head -10 >> "$REPORT_FILE"
else
    echo "No package manager detected" >> "$REPORT_FILE"
fi

echo >> "$REPORT_FILE"

# Check failed login attempts
echo "Recent failed login attempts:" >> "$REPORT_FILE"
if [[ -f /var/log/auth.log ]]; then
    grep "Failed password" /var/log/auth.log | tail -10 >> "$REPORT_FILE" 2>/dev/null || \
    echo "No failed login attempts or log not accessible" >> "$REPORT_FILE"
elif [[ -f /var/log/secure ]]; then
    grep "authentication failure" /var/log/secure | tail -10 >> "$REPORT_FILE" 2>/dev/null || \
    echo "No failed login attempts or log not accessible" >> "$REPORT_FILE"  
else
    echo "Authentication logs not found" >> "$REPORT_FILE"
fi

echo >> "$REPORT_FILE"

# 5. File System Security  
echo "📁 FILE SYSTEM SECURITY" >> "$REPORT_FILE"
echo "-----------------------" >> "$REPORT_FILE"

# Check for files with dangerous permissions
echo "Files with world-writable permissions:" >> "$REPORT_FILE"
find /opt/dohodometr -type f -perm -002 2>/dev/null | head -10 >> "$REPORT_FILE" || \
echo "No world-writable files found or directory not accessible" >> "$REPORT_FILE"

echo >> "$REPORT_FILE"

# Check for SUID/SGID files
echo "SUID/SGID files in application directory:" >> "$REPORT_FILE"
find /opt/dohodometr -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null >> "$REPORT_FILE" || \
echo "No SUID/SGID files found or directory not accessible" >> "$REPORT_FILE"

echo >> "$REPORT_FILE"

echo "✅ Infrastructure audit completed: $REPORT_FILE"
EOF

chmod +x "$AUDIT_DIR/scripts/infrastructure_audit.sh"

# 3. Compliance Audit Template  
echo -e "${BLUE}📜 Creating compliance audit template...${NC}"
cat > "$TEMPLATES_DIR/compliance_audit.md" << 'EOF'
# 📜 Compliance Audit Report - 152-ФЗ "О персональных данных"

**Organization:** Dohodometr  
**Audit Date:** ________________  
**Auditor:** ________________  
**Scope:** Personal Data Processing System

## 📋 REGULATORY REQUIREMENTS

### 1. Legal Basis for Processing (Art. 6 152-ФЗ)
- [ ] Legal basis for processing identified and documented
- [ ] User consent obtained where required
- [ ] Legitimate interests documented
- [ ] Processing limited to stated purposes

**Findings:** ________________

### 2. Data Minimization (Art. 5 152-ФЗ)  
- [ ] Only necessary personal data collected
- [ ] Data collection limited to stated purposes
- [ ] Regular review of data necessity
- [ ] Data deletion when no longer needed

**Findings:** ________________

### 3. Data Subject Rights (Art. 14 152-ФЗ)
- [ ] Right to information implemented
- [ ] Right of access implemented  
- [ ] Right to rectification implemented
- [ ] Right to deletion implemented
- [ ] Right to data portability implemented

**Findings:** ________________

### 4. Security Measures (Art. 19 152-ФЗ)
- [ ] Organizational measures implemented
- [ ] Technical measures implemented
- [ ] Access control systems in place
- [ ] Data encryption implemented
- [ ] Backup and recovery procedures

**Findings:** ________________

### 5. Data Breach Response (Art. 21 152-ФЗ)
- [ ] Incident response plan exists
- [ ] Breach notification procedures
- [ ] Impact assessment process  
- [ ] Stakeholder notification procedures
- [ ] Documentation requirements met

**Findings:** ________________

## 🔒 TECHNICAL COMPLIANCE

### Encryption Requirements
- [ ] Personal data encrypted at rest (AES-256 or equivalent)
- [ ] Data encrypted in transit (TLS 1.2+)
- [ ] Key management system implemented
- [ ] Access to encryption keys controlled
- [ ] Regular key rotation performed

**Technical Details:** ________________

### Access Control
- [ ] Role-based access control implemented
- [ ] Principle of least privilege enforced
- [ ] Regular access reviews conducted
- [ ] User authentication mechanisms
- [ ] Multi-factor authentication where required

**Access Control Matrix:** ________________

### Logging and Monitoring
- [ ] All access to personal data logged
- [ ] Log integrity protection implemented
- [ ] Regular log review performed
- [ ] Anomaly detection systems
- [ ] Log retention policies compliant

**Monitoring Coverage:** ________________

## 📊 DATA INVENTORY

### Categories of Personal Data
- [ ] Identity data (names, addresses, phone numbers)
- [ ] Financial data (bank accounts, transaction history)
- [ ] Technical data (IP addresses, device information)
- [ ] Usage data (application usage patterns)

### Data Flows
```
Data Collection → Processing → Storage → Transmission → Deletion
      ↓              ↓           ↓           ↓            ↓
   [Consent]    [Purpose]   [Security]  [Encryption]  [Verified]
```

### Third-Party Processors
- [ ] Processor agreements in place
- [ ] Processor security assessments conducted
- [ ] Data transfer mechanisms compliant
- [ ] International transfers properly governed

## 🛡️ RISK ASSESSMENT

### High Risks Identified
1. ________________
2. ________________ 
3. ________________

### Medium Risks Identified
1. ________________
2. ________________
3. ________________

### Risk Mitigation Measures
- [ ] Technical safeguards implemented
- [ ] Organizational measures in place
- [ ] Regular security assessments
- [ ] Incident response capability
- [ ] Staff training programs

## 📈 COMPLIANCE SCORE

**Categories:**
- Legal Compliance: ___/25
- Technical Security: ___/25
- Data Protection: ___/25
- Process & Documentation: ___/25

**TOTAL SCORE:** ___/100

**COMPLIANCE LEVEL:**
- 90-100: Full Compliance ✅
- 80-89: Substantial Compliance ⚠️
- 70-79: Partial Compliance ❌
- <70: Non-Compliance 🚨

## 📋 RECOMMENDATIONS

### Critical Actions (0-30 days)
1. ________________
2. ________________
3. ________________

### High Priority (1-3 months)
1. ________________
2. ________________
3. ________________

### Medium Priority (3-6 months)
1. ________________
2. ________________
3. ________________

## 📝 CONCLUSION

**Overall Assessment:** ________________

**Regulatory Status:** ________________

**Next Audit Date:** ________________

---

**Auditor Signature:** ________________  
**Date:** ________________  
**Certification:** ________________
EOF

# 4. Automated Security Scan Script
echo -e "${BLUE}🤖 Creating automated security scan script...${NC}"
cat > "$AUDIT_DIR/scripts/automated_security_scan.py" << 'EOF'
#!/usr/bin/env python3
"""
Automated Security Scan for Dohodometr
Performs comprehensive security analysis
"""

import os
import json
import subprocess
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any
import re

class SecurityScanner:
    """Automated security scanner"""
    
    def __init__(self, target_url: str, report_dir: str):
        self.target_url = target_url
        self.report_dir = report_dir
        self.logger = logging.getLogger(__name__)
        
        # Create report directory
        os.makedirs(report_dir, exist_ok=True)
        
        # Scan results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "target": target_url,
            "scans": {}
        }
    
    def run_all_scans(self) -> Dict[str, Any]:
        """Run all security scans"""
        self.logger.info("Starting comprehensive security scan...")
        
        # Code security scan
        self.results["scans"]["code"] = self.scan_code_security()
        
        # Dependency scan
        self.results["scans"]["dependencies"] = self.scan_dependencies()
        
        # Web application scan
        self.results["scans"]["web"] = self.scan_web_security()
        
        # Configuration scan
        self.results["scans"]["config"] = self.scan_configuration()
        
        # Infrastructure scan
        self.results["scans"]["infrastructure"] = self.scan_infrastructure()
        
        # Generate report
        self.generate_report()
        
        return self.results
    
    def scan_code_security(self) -> Dict[str, Any]:
        """Scan code for security vulnerabilities"""
        self.logger.info("Scanning code security...")
        
        results = {
            "status": "completed",
            "findings": [],
            "tools": []
        }
        
        # Bandit scan for Python
        try:
            cmd = ["bandit", "-r", "backend/app/", "-f", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 or result.returncode == 1:  # 1 = findings
                bandit_results = json.loads(result.stdout)
                results["tools"].append({
                    "name": "bandit",
                    "status": "success",
                    "issues": len(bandit_results.get("results", []))
                })
                results["findings"].extend(bandit_results.get("results", []))
            else:
                results["tools"].append({
                    "name": "bandit", 
                    "status": "failed",
                    "error": result.stderr
                })
        except FileNotFoundError:
            results["tools"].append({
                "name": "bandit",
                "status": "not_installed"
            })
        
        # ESLint security scan for JavaScript/TypeScript
        try:
            cmd = ["npx", "eslint", "--config", ".eslintrc.security.js", 
                   "--format", "json", "frontend/"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            if result.returncode == 0 or result.returncode == 1:
                eslint_results = json.loads(result.stdout)
                security_issues = []
                
                for file_result in eslint_results:
                    for message in file_result.get("messages", []):
                        if "security" in message.get("ruleId", "").lower():
                            security_issues.append(message)
                
                results["tools"].append({
                    "name": "eslint-security",
                    "status": "success", 
                    "issues": len(security_issues)
                })
                results["findings"].extend(security_issues)
            else:
                results["tools"].append({
                    "name": "eslint-security",
                    "status": "failed",
                    "error": result.stderr
                })
        except FileNotFoundError:
            results["tools"].append({
                "name": "eslint-security",
                "status": "not_installed"
            })
        
        return results
    
    def scan_dependencies(self) -> Dict[str, Any]:
        """Scan dependencies for vulnerabilities"""
        self.logger.info("Scanning dependencies...")
        
        results = {
            "status": "completed",
            "findings": [],
            "tools": []
        }
        
        # Python dependencies with pip-audit
        try:
            cmd = ["pip-audit", "--format=json", "--requirement", "backend/requirements.txt"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 or result.returncode == 1:
                pip_results = json.loads(result.stdout)
                results["tools"].append({
                    "name": "pip-audit",
                    "status": "success",
                    "vulnerabilities": len(pip_results.get("vulnerabilities", []))
                })
                results["findings"].extend(pip_results.get("vulnerabilities", []))
            else:
                results["tools"].append({
                    "name": "pip-audit",
                    "status": "failed", 
                    "error": result.stderr
                })
        except FileNotFoundError:
            results["tools"].append({
                "name": "pip-audit",
                "status": "not_installed"
            })
        
        # Node.js dependencies with npm audit
        try:
            cmd = ["npm", "audit", "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd="frontend/")
            
            if result.returncode == 0 or result.returncode == 1:
                npm_results = json.loads(result.stdout)
                results["tools"].append({
                    "name": "npm-audit",
                    "status": "success",
                    "vulnerabilities": npm_results.get("metadata", {}).get("vulnerabilities", {})
                })
                
                # Extract vulnerability details
                for vuln_id, vuln_data in npm_results.get("vulnerabilities", {}).items():
                    results["findings"].append({
                        "id": vuln_id,
                        "severity": vuln_data.get("severity"),
                        "title": vuln_data.get("title"),
                        "url": vuln_data.get("url")
                    })
            else:
                results["tools"].append({
                    "name": "npm-audit",
                    "status": "failed",
                    "error": result.stderr
                })
        except FileNotFoundError:
            results["tools"].append({
                "name": "npm-audit", 
                "status": "not_installed"
            })
        
        return results
    
    def scan_web_security(self) -> Dict[str, Any]:
        """Scan web application security"""
        self.logger.info("Scanning web security...")
        
        results = {
            "status": "completed",
            "findings": [],
            "headers": {},
            "endpoints": {}
        }
        
        # Check security headers
        try:
            response = requests.get(self.target_url, timeout=10)
            results["headers"] = dict(response.headers)
            
            # Check for security headers
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000',
                'Content-Security-Policy': 'default-src',
                'Referrer-Policy': 'strict-origin-when-cross-origin'
            }
            
            missing_headers = []
            for header, expected in security_headers.items():
                if header not in response.headers:
                    missing_headers.append(header)
                elif expected not in response.headers[header]:
                    results["findings"].append({
                        "type": "weak_security_header",
                        "header": header,
                        "value": response.headers[header],
                        "expected": expected
                    })
            
            if missing_headers:
                results["findings"].append({
                    "type": "missing_security_headers",
                    "headers": missing_headers
                })
                
        except requests.RequestException as e:
            results["findings"].append({
                "type": "connection_error",
                "error": str(e)
            })
        
        # Test common endpoints
        test_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/portfolios", 
            "/api/v1/transactions",
            "/admin",
            "/.env",
            "/config.json"
        ]
        
        for endpoint in test_endpoints:
            try:
                url = f"{self.target_url}{endpoint}"
                response = requests.get(url, timeout=5)
                results["endpoints"][endpoint] = {
                    "status_code": response.status_code,
                    "accessible": response.status_code < 400
                }
                
                # Check for sensitive information exposure
                if endpoint in ["/.env", "/config.json"] and response.status_code == 200:
                    results["findings"].append({
                        "type": "sensitive_file_exposed",
                        "endpoint": endpoint,
                        "severity": "critical"
                    })
                    
            except requests.RequestException:
                results["endpoints"][endpoint] = {
                    "status_code": None,
                    "accessible": False
                }
        
        return results
    
    def scan_configuration(self) -> Dict[str, Any]:
        """Scan configuration security"""
        self.logger.info("Scanning configuration...")
        
        results = {
            "status": "completed",
            "findings": []
        }
        
        # Check for hardcoded secrets in code
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']{8,}["\']',
            r'secret\s*=\s*["\'][^"\']{16,}["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']{16,}["\']',
            r'token\s*=\s*["\'][^"\']{16,}["\']'
        ]
        
        # Scan Python files
        for root, dirs, files in os.walk("backend/app"):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in secret_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                results["findings"].append({
                                    "type": "potential_hardcoded_secret",
                                    "file": file_path,
                                    "pattern": pattern,
                                    "matches": len(matches)
                                })
                    except Exception:
                        continue
        
        # Check environment files
        env_files = [".env", ".env.example", ".env.local", ".env.production"]
        for env_file in env_files:
            if os.path.exists(env_file):
                try:
                    with open(env_file, 'r') as f:
                        content = f.read()
                        
                    # Check for weak default values
                    weak_values = ["password", "secret", "admin", "123456"]
                    for line in content.split('\n'):
                        if '=' in line and not line.strip().startswith('#'):
                            key, value = line.split('=', 1)
                            value = value.strip().strip('"\'')
                            if value.lower() in weak_values:
                                results["findings"].append({
                                    "type": "weak_default_value",
                                    "file": env_file,
                                    "key": key,
                                    "value": value
                                })
                except Exception:
                    continue
        
        return results
    
    def scan_infrastructure(self) -> Dict[str, Any]:
        """Scan infrastructure security"""
        self.logger.info("Scanning infrastructure...")
        
        results = {
            "status": "completed",
            "findings": [],
            "services": {}
        }
        
        # Check Docker containers
        try:
            cmd = ["docker", "ps", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                containers = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        containers.append(json.loads(line))
                
                results["services"]["containers"] = len(containers)
                
                # Check for containers running as root
                for container in containers:
                    container_name = container.get("Names")
                    try:
                        user_cmd = ["docker", "exec", container_name, "whoami"]
                        user_result = subprocess.run(user_cmd, capture_output=True, text=True)
                        
                        if user_result.returncode == 0 and user_result.stdout.strip() == "root":
                            results["findings"].append({
                                "type": "container_running_as_root",
                                "container": container_name,
                                "severity": "medium"
                            })
                    except Exception:
                        continue
                        
        except FileNotFoundError:
            results["services"]["docker"] = "not_available"
        
        return results
    
    def generate_report(self):
        """Generate comprehensive security report"""
        report_file = os.path.join(self.report_dir, "security_audit_report.json")
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate summary report
        summary_file = os.path.join(self.report_dir, "SECURITY_AUDIT_SUMMARY.md")
        with open(summary_file, 'w') as f:
            f.write(self._generate_markdown_summary())
        
        self.logger.info(f"Reports generated: {report_file}, {summary_file}")
    
    def _generate_markdown_summary(self) -> str:
        """Generate markdown summary report"""
        
        total_findings = sum(len(scan.get("findings", [])) for scan in self.results["scans"].values())
        
        summary = f"""# 🔍 Internal Security Audit Report

**Target:** {self.results["target"]}  
**Date:** {self.results["timestamp"]}  
**Total Findings:** {total_findings}

## 📊 Scan Summary

"""
        
        for scan_name, scan_data in self.results["scans"].items():
            findings_count = len(scan_data.get("findings", []))
            status = scan_data.get("status", "unknown")
            
            summary += f"### {scan_name.title()} Security\n"
            summary += f"- **Status:** {status}\n"
            summary += f"- **Findings:** {findings_count}\n"
            
            if "tools" in scan_data:
                summary += "- **Tools:** " + ", ".join([
                    f"{tool['name']} ({tool['status']})" 
                    for tool in scan_data["tools"]
                ]) + "\n"
            
            summary += "\n"
        
        summary += """## 🎯 Recommendations

### Immediate Actions
- Review and fix all critical findings
- Update vulnerable dependencies  
- Implement missing security headers
- Remove hardcoded secrets

### Next Steps
- Schedule regular security scans
- Implement automated vulnerability monitoring
- Conduct penetration testing
- Update security documentation

---

*Report generated by Dohodometr Security Scanner*
"""
        
        return summary

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dohodometr Security Scanner")
    parser.add_argument("--target", default="http://localhost:8000", help="Target URL")
    parser.add_argument("--output", default="security_scan_results", help="Output directory")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    scanner = SecurityScanner(args.target, args.output)
    results = scanner.run_all_scans()
    
    print(f"✅ Security scan completed. Results in: {args.output}")
EOF

chmod +x "$AUDIT_DIR/scripts/automated_security_scan.py"

# 5. Master audit script
echo -e "${BLUE}🎯 Creating master audit script...${NC}"
cat > "$AUDIT_DIR/run_full_audit.sh" << 'EOF'
#!/bin/bash

# 🎯 Full Internal Security Audit for Dohodometr
# Runs comprehensive security audit

set -euo pipefail

REPORT_DIR="reports/$(date +%Y%m%d_%H%M%S)"
TARGET_URL="${1:-http://localhost:8000}"

echo "🔍 Starting Full Internal Security Audit"
echo "========================================="
echo "Target: $TARGET_URL"
echo "Report Directory: $REPORT_DIR"
echo

mkdir -p "$REPORT_DIR"

# 1. Infrastructure Audit
echo "🏗️ Running Infrastructure Audit..."
./scripts/infrastructure_audit.sh "$REPORT_DIR/infrastructure_audit.txt"

# 2. Automated Security Scan
echo "🤖 Running Automated Security Scan..."
python3 ./scripts/automated_security_scan.py --target "$TARGET_URL" --output "$REPORT_DIR/security_scan"

# 3. Code Review (Manual checklist)
echo "📋 Code Security Checklist available at:"
echo "   templates/code_security_checklist.md"

# 4. Compliance Audit (Manual checklist)  
echo "📜 Compliance Audit Checklist available at:"
echo "   templates/compliance_audit.md"

# 5. Generate Master Report
echo "📊 Generating Master Audit Report..."
cat > "$REPORT_DIR/MASTER_AUDIT_REPORT.md" << EOL
# 🔍 Master Internal Security Audit Report

**Date:** $(date)  
**Target:** $TARGET_URL  
**Auditor:** Internal Security Team

## 📋 Audit Components

### ✅ Completed Automatically
- [x] Infrastructure Security Audit
- [x] Automated Code Security Scan  
- [x] Dependency Vulnerability Scan
- [x] Web Application Security Scan
- [x] Configuration Security Review

### 📋 Manual Review Required
- [ ] Code Security Checklist (templates/code_security_checklist.md)
- [ ] Compliance Audit (templates/compliance_audit.md)  
- [ ] Penetration Testing Results
- [ ] Security Policy Review
- [ ] Training Records Review

## 📁 Report Files

### Infrastructure
- \`infrastructure_audit.txt\` - System security analysis

### Security Scan
- \`security_scan/security_audit_report.json\` - Detailed findings
- \`security_scan/SECURITY_AUDIT_SUMMARY.md\` - Executive summary

## 🎯 Next Steps

1. **Review all automated findings**
2. **Complete manual audit checklists**  
3. **Prioritize and remediate findings**
4. **Schedule follow-up testing**
5. **Update security documentation**

## 📊 Summary Dashboard

| Component | Status | Findings | Severity |
|-----------|--------|----------|----------|
| Infrastructure | ✅ Complete | See report | TBD |
| Code Security | ✅ Complete | See report | TBD |
| Dependencies | ✅ Complete | See report | TBD |
| Web Security | ✅ Complete | See report | TBD |
| Configuration | ✅ Complete | See report | TBD |
| Compliance | 📋 Manual | Pending | - |

---

*Audit completed: $(date)*
EOL

echo
echo "✅ Full Internal Security Audit Completed!"
echo "=========================================="
echo
echo "📁 All reports available in: $REPORT_DIR/"
echo "📊 Master report: $REPORT_DIR/MASTER_AUDIT_REPORT.md"
echo
echo "📋 Next Steps:"
echo "  1. Review: $REPORT_DIR/MASTER_AUDIT_REPORT.md"
echo "  2. Complete manual checklists"
echo "  3. Address identified findings"
echo "  4. Schedule regular audits"
echo
echo "🎉 Happy auditing! 🔍"
EOF

chmod +x "$AUDIT_DIR/run_full_audit.sh"

# Make all scripts executable
find "$AUDIT_DIR" -name "*.sh" -exec chmod +x {} \;

echo
echo -e "${GREEN}✅ Internal Security Audit Setup Completed!${NC}"
echo "=================================================="
echo -e "${BLUE}📁 Created audit framework:${NC}"
echo "  - Code security checklist"
echo "  - Infrastructure audit script"
echo "  - Compliance audit template"  
echo "  - Automated security scanner"
echo "  - Master audit orchestration"
echo
echo -e "${YELLOW}📋 Quick Start:${NC}"
echo "  Run full audit: ./$AUDIT_DIR/run_full_audit.sh"
echo "  Or individual components:"
echo "    Infrastructure: ./$AUDIT_DIR/scripts/infrastructure_audit.sh"
echo "    Security scan: python3 ./$AUDIT_DIR/scripts/automated_security_scan.py"
echo
echo -e "${BLUE}📖 Manual checklists:${NC}"
echo "  Code review: $TEMPLATES_DIR/code_security_checklist.md"
echo "  Compliance: $TEMPLATES_DIR/compliance_audit.md"
echo
echo -e "${GREEN}🎉 Ready for comprehensive internal security auditing!${NC}"
