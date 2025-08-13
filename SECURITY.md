# 🔒 Security Policy

## 🛡️ Security Commitment

We take the security of Investment Service seriously. We appreciate your efforts to responsibly disclose any vulnerabilities you find.

## 📋 Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | ✅ Yes             |
| 0.9.x   | ✅ Yes (until EOL) |
| < 0.9   | ❌ No              |

## 🚨 Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### 📧 Contact Information

**Primary Contact:** security@investment-service.ru

**Alternative Contact:** For urgent security issues, you can also reach us via:
- Encrypted email using our PGP key (available on request)
- GitHub Security Advisories (private disclosure)

### 📝 What to Include

When reporting a vulnerability, please include:

1. **Type of vulnerability** (e.g., SQL injection, XSS, authentication bypass)
2. **Affected component(s)** (backend, frontend, infrastructure)
3. **Potential impact** and severity assessment
4. **Steps to reproduce** (without exploiting)
5. **Affected versions** or commit hashes
6. **Your contact information** for follow-up

### 🔍 What NOT to Include

**Please avoid:**
- Detailed exploitation techniques
- Proof-of-concept code that could be malicious
- Accessing or modifying data that doesn't belong to you
- Performing DoS attacks or load testing
- Social engineering our team members

## ⏱️ Response Timeline

| Timeframe | Action |
|-----------|--------|
| 24 hours | Initial acknowledgment |
| 72 hours | Preliminary assessment |
| 7 days | Detailed analysis and plan |
| 30 days | Fix deployment (critical issues) |
| 90 days | Fix deployment (non-critical) |

## 🔄 Disclosure Process

1. **Report received** - We acknowledge receipt within 24 hours
2. **Initial triage** - We assess severity and impact within 72 hours
3. **Detailed analysis** - We investigate and develop a fix plan
4. **Fix development** - We create and test the security patch
5. **Coordinated disclosure** - We coordinate release timeline with you
6. **Public disclosure** - We publish security advisory after fix deployment

## 🏆 Recognition Program

We believe in recognizing security researchers who help improve our security:

### 🎖️ Hall of Fame

Contributors who responsibly disclose vulnerabilities will be:
- Listed in our security hall of fame (with permission)
- Credited in security advisories
- Acknowledged in release notes

### 🎁 Bounty Guidelines

While we don't currently offer monetary rewards, we provide:
- Public recognition and thanks
- Investment Service merchandise
- Direct communication with our development team
- Consideration for future security consulting opportunities

## 🔐 Security Features

### 🛡️ Current Security Measures

**Authentication & Authorization:**
- JWT tokens with refresh mechanism
- Two-factor authentication (TOTP)
- Role-based access control (RBAC)
- Session management and timeout

**Data Protection:**
- AES-256-GCM encryption for sensitive data
- Argon2id password hashing
- TLS 1.2+ encryption in transit
- Database connection encryption

**Infrastructure Security:**
- Docker container isolation
- Reverse proxy with security headers
- Rate limiting and DDoS protection
- Regular security updates

**Monitoring & Logging:**
- Security event logging
- Failed authentication tracking
- Anomaly detection
- Audit trail for sensitive operations

### 🔍 Security Testing

We implement multiple layers of security testing:
- **SAST** (Static Application Security Testing)
- **DAST** (Dynamic Application Security Testing)
- **Dependency scanning** for known vulnerabilities
- **Container image scanning**
- **Infrastructure security scanning**

## 🚫 Security Scope

### ✅ In Scope

- Backend API vulnerabilities
- Frontend application security
- Authentication and authorization flaws
- Data exposure vulnerabilities
- Infrastructure configuration issues
- Dependency vulnerabilities

### ❌ Out of Scope

- Social engineering attacks
- Physical security issues
- Third-party service vulnerabilities
- Vulnerabilities in development/staging environments
- Rate limiting bypass (unless leading to DoS)
- Issues requiring physical access to user devices

## 📋 Security Best Practices for Contributors

### 🔐 Secure Development

**Authentication:**
```python
# ✅ Good: Proper password validation
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ❌ Bad: Plain text password comparison
if password == stored_password:  # Never do this!
```

**Input Validation:**
```python
# ✅ Good: Proper input validation
from pydantic import BaseModel, validator

class CreatePortfolioRequest(BaseModel):
    name: str
    description: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) > 100:
            raise ValueError('Name too long')
        return v.strip()

# ❌ Bad: No validation
def create_portfolio(name: str):
    # Direct database insertion without validation
    cursor.execute(f"INSERT INTO portfolios (name) VALUES ('{name}')")
```

**SQL Injection Prevention:**
```python
# ✅ Good: Parameterized queries
async def get_portfolio(portfolio_id: int, user_id: int):
    query = select(Portfolio).where(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == user_id
    )
    return await session.execute(query)

# ❌ Bad: String concatenation
def get_portfolio(portfolio_id: str):
    query = f"SELECT * FROM portfolios WHERE id = {portfolio_id}"
    return cursor.execute(query)
```

### 🌐 Frontend Security

**XSS Prevention:**
```tsx
// ✅ Good: Proper escaping
import DOMPurify from 'dompurify';

const SafeHTML: React.FC<{ content: string }> = ({ content }) => {
  const sanitized = DOMPurify.sanitize(content);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
};

// ❌ Bad: Direct HTML insertion
const UnsafeHTML: React.FC<{ content: string }> = ({ content }) => {
  return <div dangerouslySetInnerHTML={{ __html: content }} />;
};
```

**Secure API Calls:**
```typescript
// ✅ Good: Proper error handling and validation
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ❌ Bad: No validation or error handling
fetch(`/api/portfolio/${userInput}`)
  .then(res => res.json())
  .then(data => setData(data));
```

### 🗄️ Database Security

**Secure Migrations:**
```python
# ✅ Good: Secure column addition
def upgrade():
    op.add_column('users', sa.Column('encrypted_ssn', sa.Text(), nullable=True))
    
    # Migrate existing data with encryption
    connection = op.get_bind()
    users = connection.execute("SELECT id, ssn FROM users WHERE ssn IS NOT NULL")
    for user in users:
        encrypted_ssn = encrypt_sensitive_data(user.ssn)
        connection.execute(
            "UPDATE users SET encrypted_ssn = %s WHERE id = %s",
            (encrypted_ssn, user.id)
        )
    
    # Remove unencrypted column
    op.drop_column('users', 'ssn')
```

## 🔧 Security Configuration

### 🌐 HTTP Security Headers

```python
# FastAPI security headers middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["dohodometr.ru", "*.dohodometr.ru"])

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### 🔐 Environment Security

```bash
# .env.example - Never commit actual secrets!
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0

# ✅ Good: Use strong secrets
SECRET_KEY=$(openssl rand -hex 32)

# ❌ Bad: Weak or default secrets
SECRET_KEY=secret123
DATABASE_PASSWORD=password
```

## 📞 Emergency Response

### 🚨 Critical Vulnerability Response

If you discover a **critical vulnerability** that could lead to:
- Data breaches
- System compromise
- Financial loss
- User safety issues

**Immediate Actions:**
1. Email security@investment-service.ru with "CRITICAL" in subject
2. Include minimal reproduction steps
3. Await our immediate response
4. Do not disclose publicly until patch is available

### 🔧 Incident Response

Our security incident response includes:
1. **Detection** - Monitoring and alerting systems
2. **Analysis** - Threat assessment and impact analysis
3. **Containment** - Immediate threat mitigation
4. **Eradication** - Root cause elimination
5. **Recovery** - System restoration and monitoring
6. **Lessons Learned** - Post-incident review and improvements

## 📊 Security Metrics

We track and monitor:
- Time to vulnerability disclosure
- Time to patch deployment
- Security test coverage
- Dependency vulnerability counts
- Security training completion rates

## 📚 Security Resources

### 🔗 Helpful Links

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CVE Database](https://cve.mitre.org/)

### 📖 Security Training

We recommend security training resources:
- OWASP WebGoat
- PortSwigger Web Security Academy
- Secure Code Warrior
- Security-focused conferences and workshops

---

**Thank you for helping keep Investment Service secure! 🛡️**

## 📧 Contact

For any security-related questions or concerns:
- **Email:** security@investment-service.ru
- **PGP Key:** Available upon request
- **Response Time:** 24 hours for acknowledgment

*Last Updated: January 2025*
