# 🚀 **ДЕПЛОЙ ПОЛНОГО ПРИЛОЖЕНИЯ DOHODOMETR.RU**

## 📊 **ТЕКУЩЕЕ СОСТОЯНИЕ**

✅ **Что работает:**
- Бэкенд API: `https://dohodometr.ru/api/v1/`
- SSL сертификат от Let's Encrypt
- Базовая инфраструктура (Traefik, PostgreSQL, Redis)

❌ **Что не работает:**
- Фронтенд показывает только статическую HTML страницу
- Нет полноценного React-приложения

---

## 🎯 **РЕШЕНИЕ**

Обновить продакшен с полноценным фронтендом и бэкендом.

---

## 📋 **ПОШАГОВАЯ ИНСТРУКЦИЯ**

### **⚠️ ВАЖНО: Сначала сохраните изменения с сервера!**

Если вчера вносились изменения напрямую на сервере, их нужно сохранить:

```bash
# На сервере
ssh root@185.23.35.41
curl -O https://raw.githubusercontent.com/NickLaye/dohodometr-investment-service/main/deployment/save_server_changes.sh
chmod +x save_server_changes.sh
./save_server_changes.sh

# На локальной машине - скачиваем изменения
scp root@185.23.35.41:/opt/server_changes_*.tar.gz ./
scp root@185.23.35.41:/opt/server_changes_*_report.txt ./
```

### **1. Git Deploy (рекомендуемый способ)**

```bash
# На сервере
ssh root@185.23.35.41
curl -O https://raw.githubusercontent.com/NickLaye/dohodometr-investment-service/main/deployment/git_deploy.sh
chmod +x git_deploy.sh
./git_deploy.sh
```

### **3. На сервере: проверить структуру**
```bash
cd /opt/dohodometr
ls -la

# Должно быть:
# backend/         <- Код FastAPI
# frontend/        <- Код Next.js  
# deployment/      <- Скрипты деплоя
# .env
# docker-compose.production.yml
```

### **4. Запустить обновление**
```bash
cd /opt/dohodometr/deployment
chmod +x update_to_full_app.sh
./update_to_full_app.sh
```

---

## ⏱️ **ВРЕМЯ ВЫПОЛНЕНИЯ**

- **Скачивание:** ~2-3 минуты
- **Сборка образов:** ~5-10 минут  
- **Запуск сервисов:** ~2-3 минуты
- **Всего:** ~10-15 минут

---

## 🔍 **ПРОВЕРКА РЕЗУЛЬТАТА**

### **Проверка фронтенда:**
```bash
curl -I https://dohodometr.ru/
```
**Ожидается:** React-приложение вместо статической страницы

### **Проверка бэкенда:**
```bash
curl -s https://dohodometr.ru/api/v1/ | jq
curl -s https://dohodometr.ru/health | jq
```

### **Проверка статуса сервисов:**
```bash
cd /opt/dohodometr
docker-compose -f docker-compose.production.yml ps
```

**Должны работать:**
- dohodometr-traefik (HEALTHY)
- dohodometr-frontend (HEALTHY)
- dohodometr-backend (HEALTHY)
- dohodometr-postgres (HEALTHY)
- dohodometr-redis (HEALTHY)

---

## 🌐 **ДОСТУПНЫЕ URL ПОСЛЕ ОБНОВЛЕНИЯ**

- **🏠 Основной сайт:** https://dohodometr.ru (React приложение)
- **🔧 API:** https://dohodometr.ru/api/v1/
- **❤️ Health Check:** https://dohodometr.ru/health
- **📊 Мониторинг:** https://uptime.dohodometr.ru
- **🔧 Traefik:** https://traefik.dohodometr.ru

---

## ⚠️ **ВАЖНЫЕ ДЕЙСТВИЯ ПОСЛЕ ДЕПЛОЯ**

### **1. Смените пароли в .env**
```bash
cd /opt/dohodometr
nano .env

# Найдите строки с 'DO_change' и замените на безопасные пароли:
SECRET_KEY=ваш_секретный_ключ_32_символа
JWT_SECRET_KEY=ваш_jwt_ключ_32_символа
POSTGRES_PASSWORD=надежный_пароль_базы
REDIS_PASSWORD=надежный_пароль_redis
```

### **2. Перезапустите после смены паролей**
```bash
docker-compose -f docker-compose.production.yml restart
```

### **3. Проверьте логи**
```bash
# Логи фронтенда
docker-compose logs frontend | tail -20

# Логи бэкенда
docker-compose logs backend | tail -20

# Логи Traefik
docker-compose logs traefik | tail -20
```

---

## 🛠️ **TROUBLESHOOTING**

### **Фронтенд не билдится:**
```bash
# Проверить ошибки сборки
docker-compose logs frontend

# Пересобрать с нуля
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### **Бэкенд не стартует:**
```bash
# Проверить ошибки
docker-compose logs backend

# Проверить подключение к БД
docker-compose exec postgres psql -U postgres -d dohodometr -c "SELECT 1;"
```

### **SSL проблемы:**
```bash
# Проверить Traefik логи
docker-compose logs traefik | grep -i "acme\|letsencrypt"

# Перевыпустить сертификат
docker-compose restart traefik
```

### **Полный перезапуск:**
```bash
docker-compose down
docker-compose up -d
```

---

## 📈 **ФУНКЦИИ ПОЛНОГО ПРИЛОЖЕНИЯ**

### **Frontend (React/Next.js):**
- 🏠 Главная страница с онбордингом
- 👤 Регистрация и авторизация
- 📊 Дашборд портфелей
- 💰 Налоговый калькулятор
- 📱 Мобильная адаптация

### **Backend (FastAPI):**
- 🔐 JWT авторизация
- 📊 API для портфелей
- 💱 API для транзакций
- 📈 Аналитический модуль
- 💰 Налоговый калькулятор РФ
- 🏦 Интеграция с Тинькофф API (в разработке)

### **Infrastructure:**
- 🔒 SSL от Let's Encrypt
- 🚀 HTTP/2 поддержка
- 📊 Мониторинг и логи
- 💾 PostgreSQL + Redis
- 🔄 Автоматические перезапуски

---

## 🎯 **СЛЕДУЮЩИЕ ШАГИ**

1. ✅ **Протестировать все функции** приложения
2. ✅ **Настроить мониторинг** (Uptime Kuma)
3. ✅ **Создать бэкапы** базы данных
4. ✅ **Настроить email** уведомления
5. ✅ **Добавить интеграции** с брокерами

---

## 🏆 **РЕЗУЛЬТАТ**

После выполнения всех шагов у вас будет:

- ✅ **Полноценное веб-приложение** на https://dohodometr.ru
- ✅ **REST API** с полной документацией
- ✅ **Безопасная инфраструктура** с SSL
- ✅ **Российский налоговый модуль**
- ✅ **Готовность к масштабированию**

🚀 **Dohodometr.ru готов к работе!**
