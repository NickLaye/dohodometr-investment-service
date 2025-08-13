#!/bin/bash

# 🔍 Dohodometr Penetration Testing Suite
# Автоматизированное тестирование безопасности

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TARGET_URL="${1:-http://localhost:8000}"
REPORT_DIR="security/pentest_reports/$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}🔍 Dohodometr Penetration Testing Suite${NC}"
echo "=================================================="
echo -e "${BLUE}Target:${NC} $TARGET_URL"
echo -e "${BLUE}Report Directory:${NC} $REPORT_DIR"
echo

# Create report directory
mkdir -p "$REPORT_DIR"

# Install required tools if not present
echo -e "${BLUE}🔧 Checking/Installing security tools...${NC}"

# Check for required tools
TOOLS=("nmap" "nikto" "sqlmap" "dirb" "curl" "jq")
MISSING_TOOLS=()

for tool in "${TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [[ ${#MISSING_TOOLS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}⚠️ Missing tools: ${MISSING_TOOLS[*]}${NC}"
    echo "Installing via package manager..."
    
    if command -v brew &> /dev/null; then
        brew install nmap nikto sqlmap dirb jq
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y nmap nikto sqlmap dirb curl jq
    else
        echo -e "${RED}❌ Cannot install tools automatically${NC}"
        echo "Please install manually: ${MISSING_TOOLS[*]}"
        exit 1
    fi
fi

# Extract host and port from URL
HOST=$(echo "$TARGET_URL" | sed -e 's|^[^/]*//||' -e 's|:[0-9]*||' -e 's|/.*||')
PORT=$(echo "$TARGET_URL" | sed -e 's|^[^/]*//[^:]*:||' -e 's|/.*||')
if [[ "$PORT" == "$HOST" ]]; then
    PORT=80
fi

echo -e "${GREEN}✅ Security tools ready${NC}"
echo

# Test 1: Network Reconnaissance
echo -e "${BLUE}🌐 Test 1: Network Reconnaissance${NC}"
echo "Scanning host: $HOST, port: $PORT"

nmap -sV -sC -O -A "$HOST" -p "$PORT" > "$REPORT_DIR/nmap_scan.txt" 2>&1 &
NMAP_PID=$!

# Test 2: Web Vulnerability Scanning  
echo -e "${BLUE}🕷️ Test 2: Web Vulnerability Scanning${NC}"
nikto -h "$TARGET_URL" -output "$REPORT_DIR/nikto_scan.txt" &
NIKTO_PID=$!

# Test 3: Directory Enumeration
echo -e "${BLUE}📁 Test 3: Directory Enumeration${NC}"
dirb "$TARGET_URL" /usr/share/dirb/wordlists/common.txt -o "$REPORT_DIR/dirb_scan.txt" &
DIRB_PID=$!

# Test 4: API Endpoint Discovery
echo -e "${BLUE}🔌 Test 4: API Endpoint Discovery${NC}"
cat > "$REPORT_DIR/api_endpoints_test.txt" << EOF
# API Endpoint Security Tests

## Common API endpoints discovered:
EOF

API_ENDPOINTS=(
    "/api/v1/auth/login"
    "/api/v1/auth/register" 
    "/api/v1/auth/refresh"
    "/api/v1/portfolios"
    "/api/v1/transactions"
    "/api/v1/analytics"
    "/health"
    "/docs"
    "/openapi.json"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
    echo "Testing: $TARGET_URL$endpoint" >> "$REPORT_DIR/api_endpoints_test.txt"
    RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" "$TARGET_URL$endpoint" || echo "FAILED")
    echo "Response: $RESPONSE" >> "$REPORT_DIR/api_endpoints_test.txt"
    echo >> "$REPORT_DIR/api_endpoints_test.txt"
done

# Test 5: Authentication Bypass Attempts
echo -e "${BLUE}🔐 Test 5: Authentication Bypass Tests${NC}"
cat > "$REPORT_DIR/auth_bypass_tests.txt" << EOF
# Authentication Bypass Test Results

EOF

# Test various auth bypass techniques
AUTH_PAYLOADS=(
    "admin:admin"
    "admin:password"
    "admin:123456"
    "test@test.com:password"
    "' OR '1'='1"
    "admin' --"
    "admin' /*"
)

for payload in "${AUTH_PAYLOADS[@]}"; do
    IFS=':' read -ra CREDS <<< "$payload"
    if [[ ${#CREDS[@]} -eq 2 ]]; then
        echo "Testing credentials: ${CREDS[0]} / ${CREDS[1]}" >> "$REPORT_DIR/auth_bypass_tests.txt"
        RESULT=$(curl -s -w "HTTP_CODE:%{http_code}" \
            -X POST "$TARGET_URL/api/v1/auth/login" \
            -H "Content-Type: application/json" \
            -d "{\"email\":\"${CREDS[0]}\",\"password\":\"${CREDS[1]}\"}" || echo "FAILED")
        echo "Result: $RESULT" >> "$REPORT_DIR/auth_bypass_tests.txt"
        echo >> "$REPORT_DIR/auth_bypass_tests.txt"
    fi
done

# Test 6: SQL Injection Detection
echo -e "${BLUE}💉 Test 6: SQL Injection Detection${NC}"
echo "Running SQLMap against login endpoint..."

sqlmap -u "$TARGET_URL/api/v1/auth/login" \
    --data '{"email":"test@test.com","password":"test"}' \
    --method POST \
    --headers="Content-Type: application/json" \
    --batch --level 3 --risk 2 \
    --output-dir="$REPORT_DIR/sqlmap" &
SQLMAP_PID=$!

# Test 7: XSS Vulnerability Testing
echo -e "${BLUE}🕳️ Test 7: XSS Vulnerability Testing${NC}"
XSS_PAYLOADS=(
    "<script>alert('XSS')</script>"
    "javascript:alert('XSS')"
    "<img src=x onerror=alert('XSS')>"
    "';alert('XSS');//"
)

cat > "$REPORT_DIR/xss_tests.txt" << EOF
# XSS Vulnerability Test Results

EOF

for payload in "${XSS_PAYLOADS[@]}"; do
    echo "Testing XSS payload: $payload" >> "$REPORT_DIR/xss_tests.txt"
    
    # Test in registration endpoint
    RESULT=$(curl -s -w "HTTP_CODE:%{http_code}" \
        -X POST "$TARGET_URL/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$payload\",\"password\":\"test123\",\"first_name\":\"$payload\",\"last_name\":\"test\"}" || echo "FAILED")
    echo "Registration endpoint result: $RESULT" >> "$REPORT_DIR/xss_tests.txt"
    echo >> "$REPORT_DIR/xss_tests.txt"
done

# Test 8: Security Headers Analysis
echo -e "${BLUE}🛡️ Test 8: Security Headers Analysis${NC}"
echo "Analyzing security headers..."

curl -I "$TARGET_URL" > "$REPORT_DIR/security_headers.txt" 2>&1

cat >> "$REPORT_DIR/security_headers.txt" << EOF

# Security Headers Analysis:

Expected Headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000; includeSubDomains
- Content-Security-Policy: restrictive policy
- Referrer-Policy: strict-origin-when-cross-origin

EOF

# Test 9: Rate Limiting Tests
echo -e "${BLUE}⏱️ Test 9: Rate Limiting Tests${NC}"
echo "Testing rate limiting on login endpoint..."

cat > "$REPORT_DIR/rate_limit_tests.txt" << EOF
# Rate Limiting Test Results

EOF

echo "Sending 10 rapid requests to login endpoint..." >> "$REPORT_DIR/rate_limit_tests.txt"
for i in {1..10}; do
    RESULT=$(curl -s -w "HTTP_CODE:%{http_code}" \
        -X POST "$TARGET_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"test@test.com","password":"wrongpassword"}' || echo "FAILED")
    echo "Request $i: $RESULT" >> "$REPORT_DIR/rate_limit_tests.txt"
    sleep 0.1
done

# Test 10: SSL/TLS Configuration
echo -e "${BLUE}🔒 Test 10: SSL/TLS Configuration${NC}"
if [[ "$TARGET_URL" == https* ]]; then
    echo "Testing SSL/TLS configuration..."
    
    # Test SSL with different protocols
    for protocol in tls1 tls1_1 tls1_2 tls1_3; do
        echo "Testing $protocol:" >> "$REPORT_DIR/ssl_tests.txt"
        RESULT=$(curl -s --$protocol "$TARGET_URL" -w "HTTP_CODE:%{http_code}" || echo "FAILED")
        echo "$protocol: $RESULT" >> "$REPORT_DIR/ssl_tests.txt"
    done
else
    echo "⚠️ HTTPS not detected - SSL tests skipped" > "$REPORT_DIR/ssl_tests.txt"
fi

# Wait for background processes
echo -e "${BLUE}⏳ Waiting for scans to complete...${NC}"
wait $NMAP_PID 2>/dev/null || echo "NMap completed"
wait $NIKTO_PID 2>/dev/null || echo "Nikto completed"  
wait $DIRB_PID 2>/dev/null || echo "Dirb completed"
wait $SQLMAP_PID 2>/dev/null || echo "SQLMap completed"

echo -e "${GREEN}✅ All scans completed${NC}"

# Generate summary report
echo -e "${BLUE}📊 Generating Summary Report...${NC}"
cat > "$REPORT_DIR/SUMMARY.md" << EOF
# Penetration Testing Report - $(date)

**Target:** $TARGET_URL  
**Date:** $(date)  
**Duration:** Automated scan  

## Executive Summary

This automated penetration testing suite evaluated the security posture of the Dohodometr application.

## Tests Performed

1. ✅ Network Reconnaissance (nmap)
2. ✅ Web Vulnerability Scanning (nikto)
3. ✅ Directory Enumeration (dirb)
4. ✅ API Endpoint Discovery
5. ✅ Authentication Bypass Tests
6. ✅ SQL Injection Detection (sqlmap)
7. ✅ XSS Vulnerability Testing
8. ✅ Security Headers Analysis
9. ✅ Rate Limiting Tests
10. ✅ SSL/TLS Configuration

## Files Generated

- \`nmap_scan.txt\` - Network reconnaissance results
- \`nikto_scan.txt\` - Web vulnerability scan
- \`dirb_scan.txt\` - Directory enumeration
- \`api_endpoints_test.txt\` - API endpoint discovery
- \`auth_bypass_tests.txt\` - Authentication bypass attempts
- \`sqlmap/\` - SQL injection test results  
- \`xss_tests.txt\` - XSS vulnerability tests
- \`security_headers.txt\` - HTTP security headers analysis
- \`rate_limit_tests.txt\` - Rate limiting effectiveness
- \`ssl_tests.txt\` - SSL/TLS configuration analysis

## Recommendations

Based on automated testing:

### Critical Issues
- Review any SQL injection findings in sqlmap results
- Ensure all authentication bypass attempts failed
- Verify rate limiting is working effectively

### High Priority  
- Implement all recommended security headers
- Enable HTTPS with strong SSL/TLS configuration
- Review directory enumeration findings

### Medium Priority
- Monitor API endpoint exposure
- Implement proper error handling
- Add additional input validation

## Next Steps

1. **Manual Review:** Have security expert review all generated reports
2. **Remediation:** Fix any critical/high issues found
3. **Verification:** Re-test after fixes
4. **Documentation:** Update security documentation

## Disclaimer

This is an automated security test. Manual penetration testing by qualified security professionals is recommended for comprehensive security assessment.

Report generated: $(date)
EOF

echo
echo -e "${GREEN}🎉 Penetration Testing Completed!${NC}"
echo "=================================================="
echo -e "${BLUE}📁 Reports Directory:${NC} $REPORT_DIR"
echo -e "${BLUE}📄 Summary Report:${NC} $REPORT_DIR/SUMMARY.md"
echo
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "  1. Review all report files"
echo "  2. Address any critical findings"
echo "  3. Schedule manual penetration testing"
echo "  4. Implement additional security controls"
echo
echo -e "${BLUE}🔍 Quick Preview:${NC}"
echo "  cat $REPORT_DIR/SUMMARY.md"
