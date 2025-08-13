#!/bin/bash

# ========================================================
# 🚀 DOHODOMETR.RU - ОБНОВЛЕНИЕ ДО ПОЛНОГО ПРИЛОЖЕНИЯ
# ========================================================
# Обновляет статическую страницу до полноценного фронтенда и бэкенда
# Автор: Dohodometr Team
# Дата: 13 августа 2025

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}🚀 DOHODOMETR.RU - ОБНОВЛЕНИЕ ДО ПОЛНОГО ПРИЛОЖЕНИЯ${NC}"
echo -e "${BLUE}========================================================${NC}"

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Этот скрипт должен запускаться с правами root${NC}"
   exit 1
fi

# Переменные
DEPLOY_DIR="/opt/dohodometr"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env"

echo -e "${YELLOW}📍 Рабочая директория: $DEPLOY_DIR${NC}"

# Проверка существования директории
if [ ! -d "$DEPLOY_DIR" ]; then
    echo -e "${RED}❌ Директория $DEPLOY_DIR не существует${NC}"
    echo -e "${YELLOW}💡 Сначала запустите основной деплой скрипт${NC}"
    exit 1
fi

cd "$DEPLOY_DIR"

echo -e "${GREEN}✅ Переходим в директорию деплоя${NC}"

# Создание резервной копии
echo -e "${YELLOW}📦 Создаем резервную копию текущей конфигурации...${NC}"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp docker-compose.production.yml "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  docker-compose.production.yml не найден"
cp .env "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  .env не найден"

echo -e "${GREEN}✅ Резервная копия создана в $BACKUP_DIR${NC}"

# Остановка старых сервисов
echo -e "${YELLOW}🛑 Останавливаем текущие сервисы...${NC}"
docker-compose -f docker-compose.production.yml down || echo "⚠️  Не удалось остановить сервисы"

# Обновление docker-compose файла
echo -e "${YELLOW}📝 Обновляем конфигурацию Docker Compose...${NC}"
# Файл уже обновлен в репозитории, просто перезапишем
cat > docker-compose.production.yml << 'EOF'
version: '3.8'

services:
  # Traefik Reverse Proxy с Let's Encrypt
  traefik:
    image: traefik:v3.0
    container_name: dohodometr-traefik
    restart: unless-stopped
    command:
      # API и Dashboard
      - --api.dashboard=true
      - --api.insecure=false
      
      # Провайдеры
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --providers.docker.network=dohodometr-network
      
      # Entrypoints
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
      
      # Let's Encrypt настройки
      - --certificatesresolvers.letsencrypt.acme.tlschallenge=true
      - --certificatesresolvers.letsencrypt.acme.email=admin@dohodometr.ru
      - --certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json
      - --certificatesresolvers.letsencrypt.acme.httpchallenge=true
      - --certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web
      
      # Логирование
      - --log.level=INFO
      - --accesslog=true
      - --accesslog.filepath=/var/log/traefik/access.log
      
      # Метрики
      - --metrics.prometheus=true
      - --metrics.prometheus.addEntryPointsLabels=true
      - --metrics.prometheus.addServicesLabels=true
    
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Traefik Dashboard
    
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
      - ./logs/traefik:/var/log/traefik
    
    networks:
      - dohodometr-network
    
    labels:
      - "traefik.enable=true"
      
      # HTTP -> HTTPS глобальный редирект
      - "traefik.http.middlewares.redirect-to-https.redirectscheme.scheme=https"
      - "traefik.http.middlewares.redirect-to-https.redirectscheme.permanent=true"
      - "traefik.http.routers.http-catchall.rule=hostregexp(\`{host:.+}\`)"
      - "traefik.http.routers.http-catchall.entrypoints=web"
      - "traefik.http.routers.http-catchall.middlewares=redirect-to-https"
      
      # Traefik Dashboard (защищенный)
      - "traefik.http.routers.traefik-dashboard.rule=Host(\`traefik.dohodometr.ru\`)"
      - "traefik.http.routers.traefik-dashboard.entrypoints=websecure"
      - "traefik.http.routers.traefik-dashboard.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik-dashboard.service=api@internal"
      - "traefik.http.routers.traefik-dashboard.middlewares=traefik-auth"
      
      # Базовая аутентификация для Traefik Dashboard
      # Базовая аутентификация (СМЕНИТЕ ПАРОЛЬ!)
      - "traefik.http.middlewares.traefik-auth.basicauth.users=admin:$$2y$$10$$X8/8Z5FxJ6v2E8K4vP9zLOQ8xF7h9D6gC5b1A3e2B9f8G7h6I5j4K3l2"
      
      # Security Headers
      - "traefik.http.middlewares.secure-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.middlewares.secure-headers.headers.customresponseheaders.X-Frame-Options=DENY"
      - "traefik.http.middlewares.secure-headers.headers.customresponseheaders.X-Content-Type-Options=nosniff"
      - "traefik.http.middlewares.secure-headers.headers.customresponseheaders.Referrer-Policy=strict-origin-when-cross-origin"
      - "traefik.http.middlewares.secure-headers.headers.customresponseheaders.Strict-Transport-Security=max-age=31536000; includeSubDomains; preload"
      - "traefik.http.middlewares.secure-headers.headers.customresponseheaders.Content-Security-Policy=default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"

  # Backend API
  backend:
    image: dohodometr-backend:latest
    container_name: dohodometr-backend
    restart: unless-stopped
    build:
      context: ../backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-dohodometr}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-change_this_secret_key_in_production}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-change_this_jwt_secret_key_in_production}
      - ENVIRONMENT=production
      - DEBUG=false
      - CORS_ORIGINS=https://dohodometr.ru,https://www.dohodometr.ru
      - TRUSTED_HOSTS=dohodometr.ru,www.dohodometr.ru
    volumes:
      - ./uploads:/app/uploads
      - ./logs/backend:/app/logs
    networks:
      - dohodometr-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      
      # API Routes
      - "traefik.http.routers.dohodometr-api.rule=Host(\`dohodometr.ru\`,\`www.dohodometr.ru\`) && PathPrefix(\`/api\`)"
      - "traefik.http.routers.dohodometr-api.entrypoints=websecure"
      - "traefik.http.routers.dohodometr-api.tls.certresolver=letsencrypt"
      - "traefik.http.routers.dohodometr-api.middlewares=secure-headers"
      - "traefik.http.services.dohodometr-api.loadbalancer.server.port=8000"
      
      # Health Check
      - "traefik.http.routers.dohodometr-health.rule=Host(\`dohodometr.ru\`,\`www.dohodometr.ru\`) && Path(\`/health\`)"
      - "traefik.http.routers.dohodometr-health.entrypoints=websecure"
      - "traefik.http.routers.dohodometr-health.tls.certresolver=letsencrypt"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend (Next.js)
  frontend:
    image: dohodometr-frontend:latest
    container_name: dohodometr-frontend
    restart: unless-stopped
    build:
      context: ../frontend
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=https://dohodometr.ru/api
      - NEXT_PUBLIC_APP_NAME=Dohodometr
      - NEXT_PUBLIC_APP_URL=https://dohodometr.ru
      - NEXT_PUBLIC_ENVIRONMENT=production
    networks:
      - dohodometr-network
    depends_on:
      - backend
    labels:
      - "traefik.enable=true"
      
      # Main Website  
      - "traefik.http.routers.dohodometr-web.rule=Host(\`dohodometr.ru\`)"
      - "traefik.http.routers.dohodometr-web.entrypoints=websecure"
      - "traefik.http.routers.dohodometr-web.tls.certresolver=letsencrypt"
      - "traefik.http.routers.dohodometr-web.middlewares=secure-headers,www-redirect"
      - "traefik.http.services.dohodometr-web.loadbalancer.server.port=3000"
      
      # WWW редирект на основной домен
      - "traefik.http.routers.dohodometr-www.rule=Host(\`www.dohodometr.ru\`)"
      - "traefik.http.routers.dohodometr-www.entrypoints=websecure"
      - "traefik.http.routers.dohodometr-www.tls.certresolver=letsencrypt"
      - "traefik.http.routers.dohodometr-www.middlewares=www-redirect"
      
      # WWW to non-WWW redirect middleware
      - "traefik.http.middlewares.www-redirect.redirectregex.regex=^https://www\\.dohodometr\\.ru/(.*)"
      - "traefik.http.middlewares.www-redirect.redirectregex.replacement=https://dohodometr.ru/$\${1}"
      - "traefik.http.middlewares.www-redirect.redirectregex.permanent=true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: dohodometr-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-dohodometr}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - dohodometr-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis Cache & Sessions
  redis:
    image: redis:7-alpine
    container_name: dohodometr-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - dohodometr-network
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Мониторинг uptime
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    container_name: dohodometr-uptime
    restart: unless-stopped
    volumes:
      - uptime_data:/app/data
    networks:
      - dohodometr-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.uptime.rule=Host(\`uptime.dohodometr.ru\`)"
      - "traefik.http.routers.uptime.entrypoints=websecure"
      - "traefik.http.routers.uptime.tls.certresolver=letsencrypt"
      - "traefik.http.routers.uptime.middlewares=uptime-auth"
      - "traefik.http.services.uptime.loadbalancer.server.port=3001"
      
      # Базовая аутентификация для мониторинга
      - "traefik.http.middlewares.uptime-auth.basicauth.users=admin:$$2y$$10$$X8/8Z5FxJ6v2E8K4vP9zLOQ8xF7h9D6gC5b1A3e2B9f8G7h6I5j4K3l2"

networks:
  dohodometr-network:
    driver: bridge
    name: dohodometr-network

volumes:
  postgres_data:
    name: dohodometr-postgres-data
  redis_data:
    name: dohodometr-redis-data
  uptime_data:
    name: dohodometr-uptime-data
EOF

echo -e "${GREEN}✅ Docker Compose конфигурация обновлена${NC}"

# Обновление переменных окружения
echo -e "${YELLOW}📝 Обновляем переменные окружения...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Файл .env не найден, создаем новый${NC}"
    cat > .env << 'EOF'
# DOHODOMETR.RU PRODUCTION ENVIRONMENT
POSTGRES_DB=dohodometr
POSTGRES_USER=postgres
POSTGRES_PASSWORD=DO_change_strong_password_2025_production
REDIS_PASSWORD=DO_change_redis_password_2025_secure
SECRET_KEY=DO_change_secret_key_production_2025_very_secure
JWT_SECRET_KEY=DO_change_jwt_secret_key_production_2025_secure
ENVIRONMENT=production
DEBUG=false
EOF
else
    # Добавляем недостающие переменные в существующий .env
    if ! grep -q "SECRET_KEY=" .env; then
        echo "SECRET_KEY=DO_change_secret_key_production_2025_very_secure" >> .env
    fi
    if ! grep -q "JWT_SECRET_KEY=" .env; then
        echo "JWT_SECRET_KEY=DO_change_jwt_secret_key_production_2025_secure" >> .env
    fi
    if ! grep -q "DEBUG=" .env; then
        echo "DEBUG=false" >> .env
    fi
fi

echo -e "${GREEN}✅ Переменные окружения обновлены${NC}"

# Создание необходимых директорий
echo -e "${YELLOW}📁 Создаем необходимые директории...${NC}"
mkdir -p uploads logs/backend logs/traefik backups

echo -e "${GREEN}✅ Директории созданы${NC}"

# Проверяем наличие исходного кода
echo -e "${YELLOW}🔍 Проверяем наличие исходного кода...${NC}"
if [ ! -d "../backend" ] || [ ! -d "../frontend" ]; then
    echo -e "${RED}❌ Исходный код не найден в ../backend и ../frontend${NC}"
    echo -e "${YELLOW}💡 Необходимо скопировать код приложения на сервер${NC}"
    echo -e "${YELLOW}   Структура должна быть:${NC}"
    echo -e "${YELLOW}   /opt/dohodometr/backend/    <- Код бэкенда${NC}"
    echo -e "${YELLOW}   /opt/dohodometr/frontend/   <- Код фронтенда${NC}"
    echo -e "${YELLOW}   /opt/dohodometr/deployment/ <- Этот скрипт${NC}"
    echo ""
    echo -e "${BLUE}📋 СЛЕДУЮЩИЕ ШАГИ:${NC}"
    echo -e "${BLUE}1. Скопируйте код на сервер:${NC}"
    echo -e "${BLUE}   scp -r backend/ frontend/ root@$(hostname -I | awk '{print $1}'):/opt/dohodometr/${NC}"
    echo -e "${BLUE}2. Запустите этот скрипт снова${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Исходный код найден${NC}"

# Сборка и запуск
echo -e "${YELLOW}🔨 Собираем и запускаем приложение...${NC}"
echo -e "${YELLOW}   Это может занять несколько минут...${NC}"

# Сначала собираем образы
docker-compose -f docker-compose.production.yml build --no-cache

# Запускаем сервисы
docker-compose -f docker-compose.production.yml up -d

echo -e "${GREEN}✅ Приложение запущено${NC}"

# Ожидание готовности сервисов
echo -e "${YELLOW}⏳ Ожидаем готовности сервисов (30 секунд)...${NC}"
sleep 30

# Проверка статуса
echo -e "${YELLOW}🔍 Проверяем статус сервисов...${NC}"
docker-compose -f docker-compose.production.yml ps

echo ""
echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО!${NC}"
echo -e "${GREEN}========================================================${NC}"
echo ""
echo -e "${GREEN}✅ Полное приложение развернуто${NC}"
echo -e "${GREEN}✅ Frontend: React/Next.js приложение${NC}"
echo -e "${GREEN}✅ Backend: FastAPI с полным функционалом${NC}"
echo -e "${GREEN}✅ Database: PostgreSQL${NC}"
echo -e "${GREEN}✅ Cache: Redis${NC}"
echo ""
echo -e "${BLUE}🌐 Доступные URL:${NC}"
echo -e "${BLUE}   Основной сайт: https://dohodometr.ru${NC}"
echo -e "${BLUE}   API: https://dohodometr.ru/api/v1/${NC}"
echo -e "${BLUE}   Health: https://dohodometr.ru/health${NC}"
echo -e "${BLUE}   Мониторинг: https://uptime.dohodometr.ru${NC}"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО: Смените пароли в .env файле!${NC}"
echo -e "${YELLOW}   Найдите строки с 'DO_change' и замените на безопасные пароли${NC}"
echo ""
echo -e "${BLUE}📋 Для проверки работоспособности:${NC}"
echo -e "${BLUE}   curl -s https://dohodometr.ru/health | jq${NC}"
echo -e "${BLUE}   curl -s https://dohodometr.ru/api/v1/ | jq${NC}"

# Финальные рекомендации
echo ""
echo -e "${GREEN}🔧 РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ:${NC}"
echo -e "${GREEN}1. Смените все пароли в .env файле${NC}"
echo -e "${GREEN}2. Настройте SSL мониторинг${NC}"
echo -e "${GREEN}3. Настройте автоматические бэкапы${NC}"
echo -e "${GREEN}4. Проверьте работу всех функций${NC}"
echo ""
echo -e "${GREEN}🎯 Готово! Dohodometr.ru теперь полноценное приложение!${NC}"
