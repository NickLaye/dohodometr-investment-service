#!/bin/bash

# 🔐 ГЕНЕРАТОР БЕЗОПАСНОГО .env ФАЙЛА ДЛЯ DOHODOMETR.RU
# Создает .env файл с криптографически стойкими паролями

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 Генерируем безопасный .env файл для продакшена${NC}"

# Функция для генерации случайного пароля
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Функция для генерации htpasswd хеша
generate_htpasswd_hash() {
    local password="$1"
    echo "admin:$(openssl passwd -apr1 "$password")"
}

# Генерируем пароли
POSTGRES_PASSWORD=$(generate_password)
REDIS_PASSWORD=$(generate_password)
SECRET_KEY=$(generate_password)
JWT_SECRET_KEY=$(generate_password)
TRAEFIK_PASSWORD=$(generate_password)
UPTIME_PASSWORD=$(generate_password)

# Генерируем хеши для базовой аутентификации
TRAEFIK_AUTH_HASH=$(generate_htpasswd_hash "$TRAEFIK_PASSWORD")
UPTIME_AUTH_HASH=$(generate_htpasswd_hash "$UPTIME_PASSWORD")

# Создаем .env файл
cat > .env << EOF
# 🚀 DOHODOMETR.RU PRODUCTION ENVIRONMENT
# Автоматически сгенерирован: $(date)
# ⚠️ КРИТИЧЕСКИ ВАЖНО: Никогда не коммитьте этот файл в Git!

# ==============================================
# 🔐 ОСНОВНАЯ БЕЗОПАСНОСТЬ
# ==============================================
SECRET_KEY=${SECRET_KEY}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENVIRONMENT=production
DEBUG=false

# ==============================================
# 💾 БАЗА ДАННЫХ POSTGRESQL
# ==============================================
POSTGRES_DB=dohodometr
POSTGRES_USER=postgres
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# ==============================================
# 📦 REDIS КЕШИРОВАНИЕ
# ==============================================
REDIS_PASSWORD=${REDIS_PASSWORD}

# ==============================================
# 🌐 СЕТЕВАЯ БЕЗОПАСНОСТЬ
# ==============================================
CORS_ORIGINS=https://dohodometr.ru,https://www.dohodometr.ru
TRUSTED_HOSTS=dohodometr.ru,www.dohodometr.ru

# ==============================================
# 🛡️ БАЗОВАЯ АУТЕНТИФИКАЦИЯ ПАНЕЛЕЙ
# ==============================================
TRAEFIK_AUTH_HASH=${TRAEFIK_AUTH_HASH}
UPTIME_AUTH_HASH=${UPTIME_AUTH_HASH}

# ==============================================
# 📧 EMAIL (настройте при необходимости)
# ==============================================
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=noreply@dohodometr.ru
SMTP_PASSWORD=CONFIGURE_EMAIL_PASSWORD

# ==============================================
# 🇷🇺 РОССИЙСКОЕ ЗАКОНОДАТЕЛЬСТВО
# ==============================================
DATA_RETENTION_DAYS=2555
STORE_DATA_IN_RF=true
TAX_RESIDENT_DEFAULT=true
NDFL_RATE=0.13
IIS_SUPPORT_ENABLED=true
LDV_CALCULATION_ENABLED=true
EOF

# Устанавливаем безопасные права доступа
chmod 600 .env

echo -e "${GREEN}✅ Безопасный .env файл создан${NC}"

# Создаем файл с паролями для администратора
cat > /tmp/dohodometr_admin_passwords.txt << EOF
# 🔐 DOHODOMETR.RU - АДМИНСКИЕ ПАРОЛИ
# Сгенерировано: $(date)
# ⚠️ КРИТИЧЕСКИ ВАЖНО: Сохраните эти пароли в безопасном месте!

==============================================
📊 СИСТЕМА ДОСТУПЫ
==============================================

PostgreSQL Database:
  Пользователь: postgres
  Пароль: ${POSTGRES_PASSWORD}

Redis Cache:
  Пароль: ${REDIS_PASSWORD}

Application Secrets:
  Secret Key: ${SECRET_KEY}
  JWT Secret: ${JWT_SECRET_KEY}

==============================================
🛠️ АДМИНИСТРАТИВНЫЕ ПАНЕЛИ
==============================================

Traefik Dashboard:
  URL: https://traefik.dohodometr.ru
  Пользователь: admin
  Пароль: ${TRAEFIK_PASSWORD}

Uptime Monitoring:
  URL: https://uptime.dohodometr.ru
  Пользователь: admin
  Пароль: ${UPTIME_PASSWORD}

==============================================
⚠️ КРИТИЧЕСКИ ВАЖНО:
==============================================
1. СОХРАНИТЕ эти пароли в безопасном менеджере паролей
2. УДАЛИТЕ этот файл после сохранения
3. НИКОГДА не передавайте пароли в открытом виде
4. РЕГУЛЯРНО меняйте пароли (раз в 6 месяцев)

rm /tmp/dohodometr_admin_passwords.txt
EOF

chmod 600 /tmp/dohodometr_admin_passwords.txt

echo -e "${YELLOW}🔐 Админские пароли сохранены в /tmp/dohodometr_admin_passwords.txt${NC}"
echo -e "${YELLOW}📝 Обязательно сохраните пароли и удалите временный файл!${NC}"
echo -e "${GREEN}✅ Настройка безопасности завершена${NC}"
