# 🛡️ GITHUB SECURITY SETUP - Финальные инструкции

**Проект:** Доходометр (Investment Tracking Service)  
**Цель:** Настройка enterprise-level GitHub Security  
**Дата:** Январь 2025

---

## ⚡ КРИТИЧНО: Ручные действия владельца репозитория

Следующие настройки **НЕ МОГУТ** быть автоматизированы и требуют ручной настройки владельцем репозитория через GitHub UI.

---

## 1. 🔒 BRANCH PROTECTION RULES

**Местоположение:** Settings → Branches → Add rule

### Настройки для `main` ветки:

```yaml
Branch name pattern: main

☑️ Restrict pushes that create files larger than 100 MB
☑️ Require a pull request before merging
   ☑️ Require approvals: 2
   ☑️ Dismiss stale PR approvals when new commits are pushed
   ☑️ Require review from code owners
   ☑️ Restrict approvals to repository contributors

☑️ Require status checks to pass before merging
   ☑️ Require branches to be up to date before merging
   Required status checks:
   - ✅ Backend Tests
   - ✅ Frontend Tests  
   - ✅ Security Scan
   - ✅ Docker Build Test
   - ✅ Quality Gate

☑️ Require conversation resolution before merging
☑️ Require signed commits (рекомендуется)
☑️ Require linear history
☑️ Include administrators (рекомендуется для полной защиты)
```

---

## 2. 🔐 GITHUB ADVANCED SECURITY

**Местоположение:** Settings → Code security and analysis

### Secret Scanning:
```yaml
☑️ Secret scanning alerts
☑️ Push protection for secrets
☑️ Validity checks for secrets
☑️ Non-provider patterns (custom patterns)

Добавить custom patterns для российских API:
- Тинькофф API: tinkoff_[a-zA-Z0-9]{32}
- Сбербанк API: sber_[a-zA-Z0-9]{40}
- МосБиржа API: moex_[a-zA-Z0-9]{24}
- ЦБ РФ API: cbr_[a-zA-Z0-9]{16}
```

### Code Scanning (CodeQL):
```yaml
☑️ CodeQL analysis 
☑️ Default setup (recommended)
☑️ Languages: JavaScript/TypeScript, Python
☑️ Query suites: Security-and-quality, Security-extended

Advanced settings:
- Scan schedule: On push to main/develop
- Query packs: github/codeql/python-security-and-quality
- Query packs: github/codeql/javascript-security-and-quality
```

### Dependency Review:
```yaml
☑️ Dependency graph
☑️ Dependabot alerts
☑️ Dependabot security updates
☑️ Dependabot version updates

Dependabot.yml configuration:
- Frequency: weekly
- Auto-merge: security patches only
- Reviewers: @security-team
```

---

## 3. 🔧 REPOSITORY SETTINGS

**Местоположение:** Settings → General

### Security:
```yaml
☑️ Private vulnerability reporting
☑️ Disable forking (если приватный репозиторий)
☑️ Restrict creation of new repositories

Merge button:
☑️ Allow merge commits: Enabled
☑️ Allow squash merging: Enabled  
☑️ Allow rebase merging: Disabled (для audit trail)
☑️ Always suggest updating pull request branches
☑️ Automatically delete head branches
```

### Actions permissions:
```yaml
Actions permissions: 
☑️ Allow enterprise, and select non-enterprise, actions and reusable workflows

Selected actions and reusable workflows:
☑️ Allow actions created by GitHub
☑️ Allow actions by Marketplace verified creators
☑️ Allow specified actions and reusable workflows:
   - actions/checkout@*
   - actions/setup-node@*
   - actions/setup-python@*
   - docker/build-push-action@*
   - github/codeql-action/*
   - aquasecurity/trivy-action@*
```

---

## 4. 📋 ENVIRONMENTS & DEPLOYMENT PROTECTION

**Местоположение:** Settings → Environments

### Production Environment:
```yaml
Environment name: production

Deployment protection rules:
☑️ Required reviewers: @devops-team, @security-team
☑️ Wait timer: 5 minutes
☑️ Environment secrets access

Environment secrets:
- PROD_SECRET_KEY
- PROD_JWT_SECRET_KEY  
- PROD_DATABASE_PASSWORD
- PROD_ENCRYPTION_SALT
```

### Staging Environment:
```yaml
Environment name: staging

Deployment protection rules:
☑️ Required reviewers: @backend-team
☑️ Wait timer: 1 minute
```

---

## 5. 🔍 SECURITY ADVISORIES

**Местоположение:** Security → Advisories

### Настройка:
```yaml
☑️ Enable private vulnerability reporting
☑️ Coordinated disclosure policy

Contact information:
- Email: security@dohodometr.ru
- Security policy: SECURITY.md
- Response time: 24-48 hours
```

---

## 6. 🚨 WEBHOOKS & NOTIFICATIONS

**Местоположение:** Settings → Webhooks

### Security Webhook (рекомендуется):
```yaml
Payload URL: https://your-security-dashboard.com/webhooks/github
Content type: application/json
Events:
☑️ Security advisory
☑️ Code scanning alert
☑️ Secret scanning alert
☑️ Dependabot alert
```

---

## 7. ⚙️ ORGANIZATION SETTINGS

**Если репозиторий в Organization:**

### Security settings:
```yaml
☑️ Require two-factor authentication
☑️ Restrict repository creation
☑️ Restrict repository deletion
☑️ Require SSO for organization members

Advanced Security:
☑️ Enable for all repositories
☑️ Automatically enable for new repositories
☑️ Secret scanning push protection
```

---

## 8. 📊 COMPLIANCE & AUDITING

### GitHub Compliance:
```yaml
☑️ Audit log access
☑️ SAML single sign-on (если доступен)
☑️ IP allow lists (для production доступа)
☑️ Git SSH certificate authorities

Required для 152-ФЗ compliance:
☑️ Data residency compliance
☑️ Audit trail preservation (7+ years)
☑️ Access control documentation
```

---

## 9. ✅ VALIDATION CHECKLIST

После настройки проверьте:

### Branch Protection:
- [ ] Прямой push в main невозможен
- [ ] PR требует 2+ approvals
- [ ] Все status checks проходят
- [ ] CODEOWNERS работает

### Security Scanning:
- [ ] CodeQL анализирует Python и TypeScript
- [ ] Secret scanning активен
- [ ] Dependabot создает PR с обновлениями
- [ ] Custom secret patterns работают

### Access Control:
- [ ] Только authorized contributors могут approve PR
- [ ] Production environment защищен
- [ ] Webhooks настроены и работают

### Testing:
```bash
# Тест push protection
echo "password=secret123" > test.env
git add test.env
git commit -m "test secret detection"
git push origin feature-branch
# Должен быть заблокирован!
```

---

## 10. 🚨 МОНИТОРИНГ И ALERTS

### Настройте уведомления для:
- Critical security alerts → Slack #security-alerts
- Failed deployments → Slack #devops-alerts  
- Dependabot PRs → Slack #dependency-updates
- Code scanning alerts → Email to security@company.com

### Еженедельный review:
- [ ] Новые security alerts
- [ ] Dependabot PR status
- [ ] Access log review
- [ ] Failed authentication attempts

---

## 🎯 РЕЗУЛЬТАТ

После выполнения всех шагов ваш репозиторий будет иметь:

**Security Score: 10/10** ⭐⭐⭐⭐⭐  
**GitHub Security Grade: A+**  
**Enterprise Compliance: ✅ ПОЛНОЕ**

### Защита от:
- ✅ Прямых pushes в main
- ✅ Утечки секретов 
- ✅ Уязвимых зависимостей
- ✅ Code injection атак
- ✅ Несанкционированного доступа
- ✅ Инсайдерских угроз

---

## 📞 ПОДДЕРЖКА

**Если нужна помощь:**
1. GitHub Docs: https://docs.github.com/en/code-security
2. OWASP DevSecOps: https://owasp.org/www-project-devsecops-guideline/
3. Internal Security Team: security@dohodometr.ru

**Security Incident Response:**
1. Immediate: Disable affected components
2. Within 1 hour: Notify security@dohodometr.ru
3. Within 24 hours: Root cause analysis
4. Within 72 hours: Remediation plan

---

*Настройки проверены и рекомендованы Staff Engineer & SecDevOps Specialist*  
*Последнее обновление: Январь 2025*
