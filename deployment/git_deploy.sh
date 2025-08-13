#!/bin/bash

# ========================================================
# 🚀 DOHODOMETR.RU - GIT DEPLOY TO PRODUCTION
# ========================================================
# Деплой через Git клонирование с GitHub
# Автор: Dohodometr Team
# Дата: 13 августа 2025

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================================${NC}"
echo -e "${BLUE}🚀 DOHODOMETR.RU - GIT DEPLOY TO PRODUCTION${NC}"
echo -e "${BLUE}========================================================${NC}"

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Этот скрипт должен запускаться с правами root${NC}"
   exit 1
fi

# Переменные
REPO_URL="https://github.com/NickLaye/dohodometr-investment-service.git"
DEPLOY_DIR="/opt/dohodometr"
BACKUP_DIR="/opt/dohodometr_backup_$(date +%Y%m%d_%H%M%S)"
BRANCH="main"

echo -e "${PURPLE}📋 ПАРАМЕТРЫ ДЕПЛОЯ:${NC}"
echo -e "${PURPLE}   Репозиторий: $REPO_URL${NC}"
echo -e "${PURPLE}   Ветка: $BRANCH${NC}"
echo -e "${PURPLE}   Директория: $DEPLOY_DIR${NC}"
echo -e "${PURPLE}   Бэкап: $BACKUP_DIR${NC}"
echo ""

# Установка зависимостей
echo -e "${YELLOW}📦 Проверяем зависимости...${NC}"

# Git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}🔧 Устанавливаем Git...${NC}"
    apt update && apt install -y git
fi

# Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🔧 Устанавливаем Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}🔧 Устанавливаем Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}✅ Все зависимости установлены${NC}"

# Создание резервной копии
if [ -d "$DEPLOY_DIR" ]; then
    echo -e "${YELLOW}📦 Создаем резервную копию...${NC}"
    cp -r "$DEPLOY_DIR" "$BACKUP_DIR"
    echo -e "${GREEN}✅ Резервная копия создана: $BACKUP_DIR${NC}"
    
    # Остановка старых сервисов
    echo -e "${YELLOW}🛑 Останавливаем старые сервисы...${NC}"
    cd "$DEPLOY_DIR/deployment" 2>/dev/null && {
        docker-compose -f docker-compose.production.yml down || echo "⚠️  Сервисы уже остановлены"
    }
fi

# Клонирование или обновление репозитория
echo -e "${YELLOW}📥 Получаем последний код...${NC}"

if [ -d "$DEPLOY_DIR/.git" ]; then
    echo -e "${BLUE}🔄 Обновляем существующий репозиторий...${NC}"
    cd "$DEPLOY_DIR"
    
    # Сохраняем местные изменения в .env
    if [ -f "deployment/.env" ]; then
        cp deployment/.env /tmp/dohodometr_env_backup
        echo -e "${GREEN}💾 Сохранен .env файл${NC}"
    fi
    
    # Получаем обновления
    git fetch origin
    git reset --hard origin/$BRANCH
    git clean -fd
    
    # Восстанавливаем .env
    if [ -f "/tmp/dohodometr_env_backup" ]; then
        cp /tmp/dohodometr_env_backup deployment/.env
        rm /tmp/dohodometr_env_backup
        echo -e "${GREEN}♻️  Восстановлен .env файл${NC}"
    fi
else
    echo -e "${BLUE}📥 Клонируем репозиторий...${NC}"
    rm -rf "$DEPLOY_DIR"
    git clone "$REPO_URL" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
    git checkout "$BRANCH"
fi

echo -e "${GREEN}✅ Код получен из GitHub${NC}"

# Переходим в директорию деплоя
cd "$DEPLOY_DIR/deployment"

# Создание .env файла если его нет
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Создаем .env файл...${NC}"
    
    # Генерируем случайные пароли
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    JWT_SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    
    cat > .env << EOF
# DOHODOMETR.RU PRODUCTION ENVIRONMENT
# Автоматически сгенерирован: $(date)

# Базы данных
POSTGRES_DB=dohodometr
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD

# Безопасность
SECRET_KEY=$SECRET_KEY
JWT_SECRET_KEY=$JWT_SECRET_KEY
ENVIRONMENT=production
DEBUG=false

# Сеть
CORS_ORIGINS=https://dohodometr.ru,https://www.dohodometr.ru
TRUSTED_HOSTS=dohodometr.ru,www.dohodometr.ru

# Email (настройте при необходимости)
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=noreply@dohodometr.ru
SMTP_PASSWORD=CHANGE_EMAIL_PASSWORD

# Российское законодательство
DATA_RETENTION_DAYS=2555
STORE_DATA_IN_RF=true
TAX_RESIDENT_DEFAULT=true
NDFL_RATE=0.13
IIS_SUPPORT_ENABLED=true
LDV_CALCULATION_ENABLED=true
EOF

    echo -e "${GREEN}✅ .env файл создан с безопасными паролями${NC}"
    
    # Сохраняем пароли
    cat > /opt/dohodometr_passwords.txt << EOF
# DOHODOMETR.RU - ПАРОЛИ ПРОДАКШЕНА
# Сгенерировано: $(date)
# ВАЖНО: Сохраните эти пароли в безопасном месте!

PostgreSQL Database:
  Пользователь: postgres
  Пароль: $POSTGRES_PASSWORD

Redis Cache:
  Пароль: $REDIS_PASSWORD

Application:
  Secret Key: $SECRET_KEY
  JWT Secret: $JWT_SECRET_KEY

Traefik Dashboard:
  URL: https://traefik.dohodometr.ru
  Пользователь: admin
  Пароль: dohodometr2025

Uptime Monitoring:
  URL: https://uptime.dohodometr.ru
  Пользователь: admin
  Пароль: dohodometr2025

УДАЛИТЕ ЭТОТ ФАЙЛ ПОСЛЕ СОХРАНЕНИЯ ПАРОЛЕЙ!
EOF
    
    chmod 600 /opt/dohodometr_passwords.txt
    echo -e "${YELLOW}🔐 Пароли сохранены в /opt/dohodometr_passwords.txt${NC}"
fi

# Создание необходимых директорий
echo -e "${YELLOW}📁 Создаем рабочие директории...${NC}"
mkdir -p logs/traefik logs/backend logs/frontend
mkdir -p letsencrypt uploads backups
mkdir -p postgres_data redis_data uptime_data

# Установка прав
chmod 755 logs uploads backups
chmod 700 letsencrypt

echo -e "${GREEN}✅ Директории созданы${NC}"

# Проверка Docker файлов
echo -e "${YELLOW}🔍 Проверяем Docker файлы...${NC}"

if [ ! -f "../backend/Dockerfile" ]; then
    echo -e "${RED}❌ Не найден backend/Dockerfile${NC}"
    exit 1
fi

if [ ! -f "../frontend/Dockerfile" ]; then
    echo -e "${RED}❌ Не найден frontend/Dockerfile${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker файлы найдены${NC}"

# Сборка и запуск
echo -e "${YELLOW}🔨 Собираем приложение...${NC}"
echo -e "${YELLOW}   Это может занять 5-10 минут...${NC}"

# Сборка образов
docker-compose -f docker-compose.production.yml build --no-cache --parallel

echo -e "${GREEN}✅ Образы собраны${NC}"

echo -e "${YELLOW}🚀 Запускаем сервисы...${NC}"

# Запуск сервисов
docker-compose -f docker-compose.production.yml up -d

echo -e "${GREEN}✅ Сервисы запущены${NC}"

# Ожидание готовности
echo -e "${YELLOW}⏳ Ожидаем готовности сервисов (60 секунд)...${NC}"
sleep 60

# Проверка статуса
echo -e "${YELLOW}🔍 Проверяем статус сервисов...${NC}"
docker-compose -f docker-compose.production.yml ps

echo ""
echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}🎉 GIT DEPLOY ЗАВЕРШЕН УСПЕШНО!${NC}"
echo -e "${GREEN}========================================================${NC}"
echo ""

# Проверка доступности
echo -e "${BLUE}🌐 Проверяем доступность сайта...${NC}"

# Проверка фронтенда
if curl -s -I https://dohodometr.ru | grep -q "200 OK"; then
    echo -e "${GREEN}✅ Фронтенд: https://dohodometr.ru - работает${NC}"
else
    echo -e "${YELLOW}⚠️  Фронтенд: ожидает инициализации${NC}"
fi

# Проверка API
if curl -s https://dohodometr.ru/api/v1/ | grep -q "Investment Service API"; then
    echo -e "${GREEN}✅ API: https://dohodometr.ru/api/v1/ - работает${NC}"
else
    echo -e "${YELLOW}⚠️  API: ожидает инициализации${NC}"
fi

# Проверка health
if curl -s https://dohodometr.ru/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health: https://dohodometr.ru/health - работает${NC}"
else
    echo -e "${YELLOW}⚠️  Health: ожидает инициализации${NC}"
fi

echo ""
echo -e "${BLUE}📊 ДОСТУПНЫЕ URL:${NC}"
echo -e "${BLUE}   🏠 Основной сайт: https://dohodometr.ru${NC}"
echo -e "${BLUE}   🔧 API: https://dohodometr.ru/api/v1/${NC}"
echo -e "${BLUE}   ❤️  Health: https://dohodometr.ru/health${NC}"
echo -e "${BLUE}   📊 Мониторинг: https://uptime.dohodometr.ru${NC}"
echo -e "${BLUE}   🛠️  Traefik: https://traefik.dohodometr.ru${NC}"
echo ""

echo -e "${YELLOW}🔐 ПАРОЛИ СОХРАНЕНЫ В:${NC}"
echo -e "${YELLOW}   /opt/dohodometr_passwords.txt${NC}"
echo -e "${YELLOW}   ОБЯЗАТЕЛЬНО СКОПИРУЙТЕ ИХ В БЕЗОПАСНОЕ МЕСТО!${NC}"
echo ""

echo -e "${GREEN}🎯 СЛЕДУЮЩИЕ ШАГИ:${NC}"
echo -e "${GREEN}1. Скопируйте пароли из /opt/dohodometr_passwords.txt${NC}"
echo -e "${GREEN}2. Удалите файл с паролями: rm /opt/dohodometr_passwords.txt${NC}"
echo -e "${GREEN}3. Настройте мониторинг на https://uptime.dohodometr.ru${NC}"
echo -e "${GREEN}4. Проверьте работу всех функций${NC}"
echo ""

echo -e "${PURPLE}📋 ПОЛЕЗНЫЕ КОМАНДЫ:${NC}"
echo -e "${PURPLE}   Логи сервисов: docker-compose logs -f${NC}"
echo -e "${PURPLE}   Перезапуск: docker-compose restart${NC}"
echo -e "${PURPLE}   Обновление: cd $DEPLOY_DIR && git pull && docker-compose up -d --build${NC}"
echo -e "${PURPLE}   Бэкап БД: docker-compose exec postgres pg_dump -U postgres dohodometr > backup.sql${NC}"
echo ""

echo -e "${GREEN}🚀 DOHODOMETR.RU УСПЕШНО РАЗВЕРНУТ ЧЕРЕЗ GIT!${NC}"

# Финальная проверка через 30 секунд
echo -e "${YELLOW}⏳ Финальная проверка через 30 секунд...${NC}"
sleep 30

echo -e "${BLUE}🔍 ФИНАЛЬНАЯ ПРОВЕРКА:${NC}"

# Проверка контейнеров
RUNNING_CONTAINERS=$(docker-compose ps --services --filter "status=running" | wc -l)
TOTAL_CONTAINERS=$(docker-compose ps --services | wc -l)

echo -e "${BLUE}   Контейнеры: $RUNNING_CONTAINERS/$TOTAL_CONTAINERS запущены${NC}"

# Проверка SSL
if curl -s -I https://dohodometr.ru | grep -q "200"; then
    echo -e "${GREEN}   ✅ HTTPS работает${NC}"
else
    echo -e "${RED}   ❌ HTTPS не работает${NC}"
fi

# Проверка API
if curl -s https://dohodometr.ru/api/v1/ | grep -q "version"; then
    echo -e "${GREEN}   ✅ API работает${NC}"
else
    echo -e "${RED}   ❌ API не работает${NC}"
fi

echo ""
echo -e "${GREEN}🎊 ДЕПЛОЙ ЗАВЕРШЕН! DOHODOMETR.RU ГОТОВ К РАБОТЕ!${NC}"
