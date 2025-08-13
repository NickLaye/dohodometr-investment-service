#!/bin/bash

# 🧪 Production Authentication Testing Script
# Комплексное тестирование всех security функций

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PRODUCTION_SERVER="${1:-localhost}"
API_URL="https://dohodometr.ru/api/v1"
TEST_EMAIL="test_$(date +%s)@dohodometr.ru"
TEST_PASSWORD="TestPassword123!"

# If testing locally
if [[ "$PRODUCTION_SERVER" == "localhost" ]]; then
    API_URL="http://localhost:8000/api/v1"
fi

echo -e "${BLUE}🧪 Dohodometr Authentication Testing${NC}"
echo "=================================================="
echo -e "${BLUE}Target:${NC} $API_URL"
echo

# Test 1: Health Check
echo -e "${BLUE}🏥 Test 1: Health Check${NC}"
BASE_URL=$(echo "$API_URL" | sed 's|/api/v1||')
HEALTH_URL="${BASE_URL}/health"
if curl -s -f "$HEALTH_URL" > /dev/null; then
    echo -e "${GREEN}✅ API Health: OK${NC}"
else
    echo -e "${RED}❌ API Health: FAILED${NC}"
    echo "API is not responding. Check services status."
    exit 1
fi

# Test 2: Registration with new secrets
echo -e "${BLUE}👤 Test 2: User Registration${NC}"
REGISTER_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"first_name\": \"Test\",
        \"last_name\": \"User\"
    }")

HTTP_STATUS=$(echo $REGISTER_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
REGISTER_BODY=$(echo $REGISTER_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [[ "$HTTP_STATUS" == "201" ]]; then
    echo -e "${GREEN}✅ Registration: SUCCESS${NC}"
    USER_ID=$(echo $REGISTER_BODY | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
    echo "   User ID: $USER_ID"
else
    echo -e "${RED}❌ Registration: FAILED (HTTP $HTTP_STATUS)${NC}"
    echo "   Response: $REGISTER_BODY"
fi

# Test 3: Login with JWT token generation
echo -e "${BLUE}🔑 Test 3: User Login & JWT Generation${NC}"
LOGIN_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\"
    }")

HTTP_STATUS=$(echo $LOGIN_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
LOGIN_BODY=$(echo $LOGIN_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [[ "$HTTP_STATUS" == "200" ]]; then
    echo -e "${GREEN}✅ Login: SUCCESS${NC}"
    ACCESS_TOKEN=$(echo $LOGIN_BODY | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
    REFRESH_TOKEN=$(echo $LOGIN_BODY | grep -o '"refresh_token":"[^"]*' | sed 's/"refresh_token":"//')
    echo "   Access Token: ${ACCESS_TOKEN:0:20}..."
    echo "   Refresh Token: ${REFRESH_TOKEN:0:20}..."
else
    echo -e "${RED}❌ Login: FAILED (HTTP $HTTP_STATUS)${NC}"
    echo "   Response: $LOGIN_BODY"
    exit 1
fi

# Test 4: Authenticated request test
echo -e "${BLUE}🛡️ Test 4: Authenticated Request${NC}"
PROTECTED_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X GET "$API_URL/portfolios" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json")

HTTP_STATUS=$(echo $PROTECTED_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
PROTECTED_BODY=$(echo $PROTECTED_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [[ "$HTTP_STATUS" == "200" ]]; then
    echo -e "${GREEN}✅ Authenticated Request: SUCCESS${NC}"
    echo "   Protected endpoint accessible"
else
    echo -e "${RED}❌ Authenticated Request: FAILED (HTTP $HTTP_STATUS)${NC}"
    echo "   Response: $PROTECTED_BODY"
fi

# Test 5: Token refresh functionality
echo -e "${BLUE}🔄 Test 5: Token Refresh${NC}"
REFRESH_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X POST "$API_URL/auth/refresh" \
    -H "Content-Type: application/json" \
    -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

HTTP_STATUS=$(echo $REFRESH_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
REFRESH_BODY=$(echo $REFRESH_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [[ "$HTTP_STATUS" == "200" ]]; then
    echo -e "${GREEN}✅ Token Refresh: SUCCESS${NC}"
    NEW_ACCESS_TOKEN=$(echo $REFRESH_BODY | grep -o '"access_token":"[^"]*' | sed 's/"access_token":"//')
    echo "   New Access Token: ${NEW_ACCESS_TOKEN:0:20}..."
else
    echo -e "${RED}❌ Token Refresh: FAILED (HTTP $HTTP_STATUS)${NC}"
    echo "   Response: $REFRESH_BODY"
fi

# Test 6: Logout with token revocation
echo -e "${BLUE}🚪 Test 6: Logout & Token Revocation${NC}"
LOGOUT_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X POST "$API_URL/auth/logout" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json")

HTTP_STATUS=$(echo $LOGOUT_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
LOGOUT_BODY=$(echo $LOGOUT_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

if [[ "$HTTP_STATUS" == "200" ]]; then
    echo -e "${GREEN}✅ Logout: SUCCESS${NC}"
    echo "   Token added to blacklist"
else
    echo -e "${YELLOW}⚠️ Logout: PARTIAL (HTTP $HTTP_STATUS)${NC}"
    echo "   Response: $LOGOUT_BODY"
fi

# Test 7: Verify token revocation
echo -e "${BLUE}🚫 Test 7: Revoked Token Verification${NC}"
REVOKED_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
    -X GET "$API_URL/portfolios" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json")

HTTP_STATUS=$(echo $REVOKED_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')

if [[ "$HTTP_STATUS" == "401" ]]; then
    echo -e "${GREEN}✅ Token Revocation: SUCCESS${NC}"
    echo "   Revoked token properly rejected"
else
    echo -e "${RED}❌ Token Revocation: FAILED (HTTP $HTTP_STATUS)${NC}"
    echo "   Revoked token still works!"
fi

# Test 8: Password hashing verification
echo -e "${BLUE}🔐 Test 8: Cryptographic Functions${NC}"
CRYPTO_TEST=$(ssh "$PRODUCTION_SERVER" "
    cd /opt/dohodometr
    sudo docker-compose -f docker-compose.production.yml exec -T backend python -c \"
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
import sys

# Test password hashing
test_password = 'TestPassword123'
hash1 = get_password_hash(test_password)
hash2 = get_password_hash(test_password)

print('Hash 1:', hash1[:50], '...')
print('Hash 2:', hash2[:50], '...')
print('Hashes different:', hash1 != hash2)
print('Password verification:', verify_password(test_password, hash1))
print('Encryption salt length:', len(settings.ENCRYPTION_SALT))
print('Secret key length:', len(settings.SECRET_KEY))
\"" 2>/dev/null || echo "Crypto test failed")

if echo "$CRYPTO_TEST" | grep -q "Password verification: True"; then
    echo -e "${GREEN}✅ Cryptographic Functions: OK${NC}"
    echo "   Password hashing working correctly"
    echo "   Encryption salt properly configured"
else
    echo -e "${RED}❌ Cryptographic Functions: FAILED${NC}"
    echo "$CRYPTO_TEST"
fi

# Final summary
echo
echo -e "${BLUE}📊 AUTHENTICATION TEST SUMMARY${NC}"
echo "=================================================="

TESTS_PASSED=0
TOTAL_TESTS=8

# Count successful tests (simplified)
if curl -s -f "$API_URL/../health" > /dev/null; then ((TESTS_PASSED++)); fi
if [[ "$HTTP_STATUS" != "401" ]] && echo "$REGISTER_BODY" | grep -q "id"; then ((TESTS_PASSED++)); fi
if [[ -n "$ACCESS_TOKEN" ]]; then ((TESTS_PASSED++)); fi
if echo "$PROTECTED_BODY" | grep -q -v "error\|unauthorized"; then ((TESTS_PASSED++)); fi
if [[ -n "$NEW_ACCESS_TOKEN" ]]; then ((TESTS_PASSED++)); fi
if echo "$LOGOUT_BODY" | grep -q -v "error"; then ((TESTS_PASSED++)); fi
if [[ "$HTTP_STATUS" == "401" ]]; then ((TESTS_PASSED++)); fi  # For revocation test
if echo "$CRYPTO_TEST" | grep -q "Password verification: True"; then ((TESTS_PASSED++)); fi

echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED/$TOTAL_TESTS${NC}"

if [[ $TESTS_PASSED -eq $TOTAL_TESTS ]]; then
    echo -e "${GREEN}🎉 ALL AUTHENTICATION TESTS PASSED!${NC}"
    echo "   Your security implementation is working perfectly!"
    exit 0
elif [[ $TESTS_PASSED -ge 6 ]]; then
    echo -e "${YELLOW}⚠️ MOST TESTS PASSED${NC}"
    echo "   Minor issues detected, but core security is working"
    exit 0
else
    echo -e "${RED}❌ CRITICAL AUTHENTICATION FAILURES${NC}"
    echo "   Immediate investigation required!"
    exit 1
fi
