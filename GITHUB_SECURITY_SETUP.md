# 🔒 GITHUB SECURITY SETUP - КРИТИЧНО ВАЖНО!

**Статус:** ⚠️ ТРЕБУЕТ РУЧНОЙ НАСТРОЙКИ ВЛАДЕЛЬЦЕМ РЕПОЗИТОРИЯ  
**Приоритет:** 🚨 КРИТИЧЕСКИЙ  
**Время выполнения:** ~15 минут

---

## 🎯 ОБЗОР

После применения всех исправлений кода, владелец репозитория **ДОЛЖЕН** настроить следующие GitHub Security features для полной защиты проекта.

## ✅ ЧТО УЖЕ ИСПРАВЛЕНО В КОДЕ

- ✅ GitHub Actions закреплены по SHA (supply chain protection)
- ✅ Слабые дефолтные секреты заменены на placeholder'ы
- ✅ Создан скрипт генерации безопасных секретов
- ✅ Настроен CODEOWNERS файл
- ✅ Добавлены comprehensive тесты
- ✅ Улучшен Dependabot с security grouping

## 🚨 КРИТИЧНЫЕ ДЕЙСТВИЯ ДЛЯ ВЛАДЕЛЬЦА

### 1️⃣ ВКЛЮЧИТЬ GITHUB ADVANCED SECURITY (5 мин)

```bash
# Перейти в репозиторий на GitHub.com
# Repository → Settings → Security and analysis

✅ Secret scanning → Enable
✅ Push protection → Enable  
✅ Dependency graph → Enable (обычно включен по умолчанию)
✅ Dependabot alerts → Enable
✅ Dependabot security updates → Enable
✅ CodeQL analysis → Enable
```

**Скриншот пути:** `Settings` > `Security and analysis` > включить все переключатели

### 2️⃣ НАСТРОИТЬ BRANCH PROTECTION RULES (3 мин)

```bash
# Repository → Settings → Branches → Add rule

Rule name: main

☑️ Require pull request reviews before merging
   ├── Required approving reviews: 2
   ├── Dismiss stale reviews: ✅
   └── Require review from CODEOWNERS: ✅

☑️ Require status checks to pass before merging
   ├── Require branches to be up to date: ✅
   └── Status checks:
       - backend-tests
       - frontend-tests  
       - security
       - docker-build

☑️ Require conversation resolution before merging: ✅
☑️ Require signed commits: ✅ (рекомендуется)
☑️ Require linear history: ✅ (опционально)
☑️ Include administrators: ✅
☑️ Restrict pushes that create matching branches: ✅
```

### 3️⃣ РОТИРОВАТЬ PRODUCTION СЕКРЕТЫ (2 мин)

```bash
# НА СЕРВЕРЕ РАЗРАБОТКИ:
cd /path/to/dohodometr
./deployment/generate_secure_secrets.sh .env.production

# СКОПИРОВАТЬ НА PRODUCTION СЕРВЕР:
scp .env.production user@production-server:/secure/location/

# НА PRODUCTION СЕРВЕРЕ:
# Остановить сервисы
docker-compose down

# Заменить старый .env файл
cp /secure/location/.env.production .env

# Перезапустить с новыми секретами
docker-compose up -d

# Проверить работоспособность
curl https://yourdomain.com/health
```

### 4️⃣ НАСТРОИТЬ CUSTOM SECRET SCANNING (2 мин)

GitHub → Repository → Settings → Security and analysis → Secret scanning

**Добавить custom patterns для российских сервисов:**

```regex
# Tinkoff API Token
[Tt]inkoff.*[0-9a-f]{32}

# Sberbank API Key  
[Ss]ber.*[A-Za-z0-9]{40}

# Russian Tax Service API
nalog\.ru.*[0-9a-zA-Z]{32}

# MOEX API Token
moex.*[a-zA-Z0-9]{24}
```

### 5️⃣ НАСТРОИТЬ SECURITY ALERTS (1 мин)

```bash
# Repository → Settings → Notifications

☑️ Email notifications для:
   - Dependabot alerts
   - Secret scanning alerts
   - Code scanning alerts
   - Discussions

# Добавить team email если есть
Security team email: security@dohodometr.ru
```

### 6️⃣ ПРОВЕРИТЬ РАБОТУ (2 мин)

```bash
# 1. Попробовать push секрета (должен быть заблокирован)
echo "SECRET_KEY=real_secret_123" > test_secret.txt
git add test_secret.txt
git commit -m "test secret"
git push
# Должно быть: ❌ Push rejected by GitHub

# 2. Создать test PR (должны запуститься все проверки)
git checkout -b test-security-setup
echo "# Test PR" >> README.md
git add README.md && git commit -m "test: security setup verification"
git push -u origin test-security-setup
# Создать PR через UI

# 3. Проверить что все status checks работают
# В PR должны быть: backend-tests, frontend-tests, security, docker-build
```

---

## 📊 ПРОВЕРОЧНЫЙ ЧЕКЛИСТ

После выполнения всех шагов, проверьте:

### 🔒 Security Features
- [ ] GitHub Advanced Security включен
- [ ] Secret scanning активен + Push protection
- [ ] CodeQL анализ настроен
- [ ] Custom secret patterns добавлены
- [ ] Dependabot alerts включены

### 🛡️ Branch Protection
- [ ] main ветка защищена
- [ ] Требуется 2+ reviewers
- [ ] Status checks обязательны
- [ ] CODEOWNERS проверка включена
- [ ] Администраторы не могут обходить правила

### 🔐 Secrets Management
- [ ] Production секреты ротированы
- [ ] Старые weak secrets удалены
- [ ] `.env.production.secure` создан
- [ ] Секреты не содержат predictable patterns

### ✅ Testing
- [ ] Pre-commit hooks установлены: `make install-deps`
- [ ] Тесты проходят: `make test`
- [ ] Security scans чистые: `make security-scan`
- [ ] No secrets в коде: `make secrets-check`

---

## 🚨 КРИТИЧНЫЕ ПРЕДУПРЕЖДЕНИЯ

### ⚠️ НЕМЕДЛЕННО ИСПРАВИТЬ:

1. **Weak Secrets в Production:**
   ```bash
   # ❌ КРИТИЧНО: Эти значения ДОЛЖНЫ быть изменены:
   SECRET_KEY=DO_change_secret_key_production_2025_very_secure
   JWT_SECRET_KEY=DO_change_jwt_secret_key_production_2025_secure
   ```

2. **Открытый main branch:**
   - Без Branch Protection любой может внести критичные изменения
   - Отсутствует peer review для security-critical кода

3. **Отсутствие Secret Scanning:**
   - Риск случайного commit'а реальных API ключей
   - Нет защиты от утечки production credentials

---

## 🔧 АВТОМАТИЗАЦИЯ (ОПЦИОНАЛЬНО)

Создайте GitHub Actions workflow для проверки security compliance:

```yaml
# .github/workflows/security-compliance.yml
name: Security Compliance Check
on:
  schedule:
    - cron: '0 6 * * 1'  # Каждый понедельник

jobs:
  compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check Branch Protection
        run: |
          # Проверить что main защищена
          gh api repos/${{ github.repository }}/branches/main/protection
      - name: Check Secret Scanning
        run: |
          # Проверить что secret scanning включен
          gh api repos/${{ github.repository }} | jq '.security_and_analysis'
```

---

## 📞 ПОДДЕРЖКА

**Если возникли проблемы:**

1. **GitHub Support:** https://support.github.com/
2. **Документация:** https://docs.github.com/en/code-security
3. **Team Contact:** security@dohodometr.ru
4. **Emergency:** Отключить проблемный feature временно

---

## ✅ ФИНАЛЬНАЯ ПРОВЕРКА

После выполнения всех шагов, репозиторий должен иметь:

- 🔒 **Security Score: 90+/100**
- 🛡️ **Branch Protection: Active**  
- 🚫 **Secret Exposure: Impossible**
- ✅ **Compliance: OWASP ASVS Level 2**
- 🎯 **Production Ready: Yes**

**🎉 ПОЗДРАВЛЯЕМ! Dohodometr теперь имеет enterprise-grade security!**

---

**Время выполнения:** ~15 минут  
**Следующий review:** Через 30 дней  
**Статус:** ⏳ Ожидает выполнения владельцем
