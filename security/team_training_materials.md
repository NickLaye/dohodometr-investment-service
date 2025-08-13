# 🎓 SECURITY TRAINING MATERIALS - Доходометр

**Цель:** Обучить команду разработки security best practices и процедурам  
**Аудитория:** Разработчики, DevOps, QA, Product менеджеры  
**Время:** 2-4 часа (можно разбить на сессии)

---

## 📋 ПРОГРАММА ОБУЧЕНИЯ

### 🔰 Модуль 1: Security Mindset (30 минут)

#### Зачем нам нужна безопасность?
- **152-ФЗ**: Штрафы до 18 млн рублей за утечку ПДн
- **Репутация**: Один инцидент = потеря доверия клиентов
- **Бизнес**: Безопасность = конкурентное преимущество

#### Security by Design
```
❌ Неправильно: "Добавим безопасность потом"
✅ Правильно: "Безопасность с первой строки кода"
```

#### Threat Modeling
- **Кто:** Хакеры, инсайдеры, конкуренты, государства
- **Что:** Данные пользователей, финансовая информация, исходный код
- **Как:** SQL injection, XSS, social engineering, insider threats

---

### 🔐 Модуль 2: Secure Coding Practices (45 минут)

#### Backend Security (Python/FastAPI)

**✅ DO:**
```python
# Безопасное хеширование паролей
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
hashed = pwd_context.hash(password)

# Параметризованные SQL запросы
def get_user(user_id: int):
    query = select(User).where(User.id == user_id)
    return session.execute(query)

# Валидация входных данных
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 12:
            raise ValueError('Password too short')
        return v
```

**❌ DON'T:**
```python
# Слабое хеширование
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()  # ❌ УЯЗВИМО

# SQL injection
def get_user(user_id: str):
    query = f"SELECT * FROM users WHERE id = {user_id}"  # ❌ ОПАСНО

# Хардкод секретов
SECRET_KEY = "my-secret-key"  # ❌ НИКОГДА

# Логирование секретов  
logger.info(f"User password: {password}")  # ❌ ОПАСНО
```

#### Frontend Security (React/TypeScript)

**✅ DO:**
```typescript
// XSS защита
import DOMPurify from 'dompurify';

const SafeHTML: React.FC<{ content: string }> = ({ content }) => {
  const sanitized = DOMPurify.sanitize(content);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
};

// Безопасное хранение токенов
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// CSRF защита
apiClient.interceptors.request.use((config) => {
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});
```

**❌ DON'T:**
```typescript
// Прямая вставка HTML
const UnsafeHTML = ({ content }: { content: string }) => (
  <div dangerouslySetInnerHTML={{ __html: content }} />  // ❌ XSS RISK
);

// Секреты в localStorage
localStorage.setItem('api_key', 'secret123');  // ❌ ДОСТУПНО ВСЕМ

// Отсутствие валидации
fetch(`/api/user/${userInput}`)  // ❌ INJECTION RISK
```

---

### 🛡️ Модуль 3: Authentication & Authorization (30 минут)

#### JWT Security Best Practices

**Правильная конфигурация:**
```python
# Короткие TTL для access токенов
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Длинные TTL для refresh токенов  
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Строгий алгоритм
JWT_ALGORITHM = "HS512"  # НЕ используйте "none" или RS256 без проверки

# JTI для revocation
def create_access_token(subject: str):
    return jwt.encode({
        "sub": subject,
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "jti": secrets.token_urlsafe(16),  # Unique ID
        "type": "access"
    }, settings.JWT_SECRET_KEY, algorithm="HS512")
```

#### 2FA Implementation
```python
# TOTP Setup
import pyotp

def setup_2fa(user: User):
    secret = pyotp.random_base32()
    totp_uri = pyotp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="Dohodometr"
    )
    return generate_qr_code(totp_uri)

def verify_2fa(user: User, token: str):
    totp = pyotp.TOTP(user.totp_secret)
    return totp.verify(token, valid_window=1)
```

---

### 🔒 Модуль 4: Data Protection & Encryption (30 минут)

#### Шифрование чувствительных данных

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def encrypt_pii(data: str) -> str:
    """Шифрование персональных данных"""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_pii(encrypted_data: str) -> str:
    """Расшифровка персональных данных"""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
    return f.decrypt(encrypted_bytes).decode()
```

#### PII Data Handling (152-ФЗ Compliance)

**Классификация данных:**
- 🔴 **Критичные ПДн**: ФИО, паспорт, СНИЛС → Обязательное шифрование
- 🟡 **Важные данные**: Email, телефон → Шифрование рекомендуется  
- 🟢 **Публичные данные**: Логи, статистика → Можно не шифровать

**Retention Policy:**
```python
class DataRetentionService:
    def __init__(self):
        self.retention_days = 2555  # 7 лет согласно 152-ФЗ
    
    def schedule_deletion(self, user_id: int):
        """Запланировать удаление через 7 лет"""
        deletion_date = datetime.now() + timedelta(days=self.retention_days)
        # Запланировать задачу удаления
```

---

### 🚨 Модуль 5: Incident Response (20 минут)

#### Security Incident Classification

**P0 - Критичный (реагировать немедленно):**
- Утечка персональных данных
- Компрометация production систем  
- DDoS атака
- Insider threat

**P1 - Высокий (реагировать в течение 2 часов):**
- Подозрительная активность в логах
- Уязвимость в production коде
- Неавторизованный доступ к системам

**P2 - Средний (реагировать в течение 24 часов):**
- Уязвимости в зависимостях
- Неправильная конфигурация безопасности
- Социальная инженерия

#### Incident Response Playbook

**Шаг 1: Обнаружение (Detection)**
```bash
# Проверить подозрительную активность
grep "Failed login" /var/log/auth.log | tail -50

# Проверить сетевые соединения
netstat -tulpn | grep LISTEN

# Проверить запущенные процессы
ps aux | grep -E "(python|node|docker)"
```

**Шаг 2: Сдерживание (Containment)**
```bash
# Заблокировать подозрительный IP
sudo ufw deny from 192.168.1.100

# Отозвать все токены пользователя
redis-cli FLUSHDB  # Очистить blacklist и начать заново

# Изолировать скомпрометированный сервис
docker stop container_name
```

**Шаг 3: Расследование (Investigation)**
- Собрать логи всех систем
- Определить timeline инцидента
- Выявить затронутые данные
- Документировать все действия

**Шаг 4: Восстановление (Recovery)**
- Применить патчи/исправления
- Ротировать скомпрометированные ключи
- Восстановить сервисы из backup
- Усилить мониторинг

**Шаг 5: Lessons Learned**
- Post-mortem meeting
- Обновить процедуры
- Улучшить детекцию
- Обучить команду

---

### 🔧 Модуль 6: DevSecOps Practices (30 минут)

#### Security в CI/CD Pipeline

**Pre-commit Hooks:**
```bash
# Установка
pip install pre-commit
pre-commit install

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        
  - repo: https://github.com/PyCQA/bandit  
    hooks:
      - id: bandit
        args: ['-r', 'app/', '-f', 'json']
```

**GitHub Actions Security:**
```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
      
    steps:
      - name: Run CodeQL
        uses: github/codeql-action/analyze@v2
        with:
          languages: python, javascript
          
      - name: Run Trivy  
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          format: 'sarif'
          output: 'trivy-results.sarif'
```

#### Secret Management

**❌ Плохо:**
```python
DATABASE_URL = "postgresql://user:password@localhost/db"
API_KEY = "abcd1234567890"
```

**✅ Хорошо:**
```python
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**🏆 Отлично (Production):**
```bash
# HashiCorp Vault
vault kv put secret/dohodometr \
    database_url="postgresql://user:pass@host/db" \
    api_key="secret123"

# AWS Secrets Manager  
aws secretsmanager create-secret \
    --name "dohodometr/database" \
    --secret-string '{"username":"user","password":"pass"}'
```

---

### 📊 Модуль 7: Security Monitoring (25 минут)

#### Что мониторить?

**Authentication Events:**
```python
# Log all auth events
def log_security_event(event_type: str, user_id: int = None, **kwargs):
    logger.info({
        "event": event_type,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": get_client_ip(),
        "user_agent": get_user_agent(),
        **kwargs
    })

# Usage
log_security_event("login_failed", details={"reason": "invalid_password"})
log_security_event("login_successful", user_id=123)
log_security_event("2fa_enabled", user_id=123)
```

**Suspicious Patterns:**
- Множественные failed login attempts
- Необычные IP адреса или локации
- API запросы в нерабочее время
- Большие объемы данных
- Админские действия

**Alerting Rules:**
```python
# Prometheus alerts
ALERT HighFailedLoginRate
  IF rate(login_failed_total[5m]) > 10
  FOR 2m
  ANNOTATIONS {
    summary = "High failed login rate detected"
  }

ALERT SuspiciousAPIUsage  
  IF rate(api_requests_total{status_code="401"}[1m]) > 50
  FOR 1m
  ANNOTATIONS {
    summary = "Possible brute force attack"
  }
```

#### Security Metrics Dashboard

**Key Metrics:**
- Failed login attempts per minute
- Active user sessions
- API error rates (4xx, 5xx)  
- Database connection anomalies
- File access patterns
- Network traffic anomalies

**Tools:**
- **Grafana**: Визуализация метрик
- **Prometheus**: Сбор метрик
- **ELK Stack**: Анализ логов
- **Slack/Email**: Alerting

---

### 🎯 Модуль 8: Security Review Process (15 минут)

#### Code Review Security Checklist

**Backend Review:**
```
□ Нет хардкода секретов
□ Все SQL запросы параметризованы  
□ Input validation присутствует
□ Authentication проверки есть
□ Logging не содержит PII
□ Error handling не раскрывает внутренние детали
□ Rate limiting настроен
□ HTTPS используется везде
```

**Frontend Review:**
```
□ XSS защита реализована
□ CSRF токены используются
□ Sensitive data не в localStorage  
□ API calls валидированы
□ Error messages не раскрывают детали
□ Content Security Policy настроен
□ Все forms валидируются
```

**Infrastructure Review:**
```
□ Secrets в environment variables
□ Контейнеры запускаются не от root
□ Network policies ограничивают трафик
□ Backup шифруется
□ Monitoring настроен
□ Log retention policy соблюдается
```

---

## 🎓 ПРАКТИЧЕСКИЕ УПРАЖНЕНИЯ

### Упражнение 1: Найти уязвимость
```python
# Код с уязвимостью - найдите проблему
def get_user_data(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)

# Ответ: SQL Injection - user_id не валидируется
```

### Упражнение 2: Исправить код
```typescript
// Небезопасный код
const UserProfile = ({ userBio }: { userBio: string }) => (
  <div dangerouslySetInnerHTML={{ __html: userBio }} />
);

// Исправленный код
const UserProfile = ({ userBio }: { userBio: string }) => {
  const sanitized = DOMPurify.sanitize(userBio);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
};
```

### Упражнение 3: Security Review
Проведите security review вашего последнего PR, используя чек-лист выше.

---

## 📚 ДОПОЛНИТЕЛЬНЫЕ РЕСУРСЫ

### Обязательное чтение:
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [152-ФЗ "О персональных данных"](http://www.consultant.ru/document/cons_doc_LAW_61801/)

### Рекомендуемые курсы:
- PortSwigger Web Security Academy (бесплатно)
- OWASP WebGoat (практические упражнения)
- Secure Code Warrior (платформа обучения)

### Tools для изучения:
- Burp Suite (web app security testing)
- OWASP ZAP (бесплатная альтернатива Burp)
- Nmap (network scanning)
- Wireshark (network analysis)

---

## ✅ ЧЕКПОИНТЫ ОБУЧЕНИЯ

После обучения каждый участник должен:

**Уровень 1 (Базовый):**
- [ ] Понимать основные принципы информационной безопасности
- [ ] Знать OWASP Top 10 уязвимостей
- [ ] Уметь безопасно хранить секреты
- [ ] Понимать процедуру incident response

**Уровень 2 (Продвинутый):**
- [ ] Проводить security review кода
- [ ] Настраивать мониторинг безопасности
- [ ] Проводить базовое penetration testing
- [ ] Разрабатывать secure API

**Уровень 3 (Экспертный):**
- [ ] Проектировать secure architecture
- [ ] Проводить threat modeling
- [ ] Настраивать advanced security controls
- [ ] Обучать других безопасности

---

## 📞 ПОДДЕРЖКА

**Security Team:**
- Email: security@dohodometr.ru
- Slack: #security-team  
- Confluence: Security Wiki

**Emergency Contact:**
- Phone: +7 (XXX) XXX-XX-XX
- 24/7 Security Hotline

---

*Материалы обновлены: Январь 2025*  
*Следующий пересмотр: Апрель 2025*
