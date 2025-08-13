# ⚡ БЫСТРАЯ ПРОВЕРКА GITHUB SECURITY

**Статус:** 🔍 Проверяем настройки  
**Время:** 2 минуты

---

## 🚨 КРИТИЧНАЯ ПРОВЕРКА - ВЫПОЛНИ СЕЙЧАС:

### 1️⃣ **Branch Protection (30 сек)**
```bash
# Перейди: GitHub Repository → Settings → Branches
# Проверь что main имеет Protection rule:

✅ Require pull request reviews: ON (2+ reviewers)
✅ Require status checks: ON  
✅ Restrict pushes: ON
✅ Include administrators: ON
```

### 2️⃣ **Secret Scanning (30 сек)**  
```bash
# Перейди: Repository → Settings → Security and analysis

✅ Secret scanning: ENABLED
✅ Push protection: ENABLED  
✅ Dependabot alerts: ENABLED
✅ CodeQL analysis: ENABLED
```

### 3️⃣ **Quick Test (30 сек)**
```bash
# Попробуй создать файл с секретом:
echo "SECRET_KEY=sk_test_123456789" > test_secret.txt
git add test_secret.txt
git commit -m "test secret"
git push

# Должно быть: ❌ "Push blocked - secret detected"
# Если push прошёл = Secret scanning НЕ работает!
```

### 4️⃣ **Status Checks (30 сек)**
```bash
# Создай test PR и проверь что запускаются:
✅ backend-tests
✅ frontend-tests  
✅ security
✅ docker-build

# Если не запускаются - проверь .github/workflows/
```

---

## ✅ ЕСЛИ ВСЁ ОК - ПЕРЕХОДИМ К СЛЕДУЮЩЕМУ ЭТАПУ!
