#!/bin/bash

echo "🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ YOUINVEST НА VPS"
echo "========================================"
echo ""
echo "Этот скрипт установит полную production версию YouInvest на ваш VPS сервер."
echo ""

# Проверка запуска от root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен запускаться от root!"
   echo "Запустите: sudo bash deploy_vps.sh"
   exit 1
fi

# Определяем OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo "❌ Не удалось определить операционную систему"
    exit 1
fi

echo "✅ Операционная система: $OS $VER"

# Проверка поддерживаемых ОС
case $OS in
    ubuntu)
        if [[ "$VER" < "20.04" ]]; then
            echo "❌ Требуется Ubuntu 20.04 или новее"
            exit 1
        fi
        ;;
    debian)
        if [[ "$VER" < "11" ]]; then
            echo "❌ Требуется Debian 11 или новее"  
            exit 1
        fi
        ;;
    centos|rhel|rocky|almalinux)
        if [[ "$VER" < "8" ]]; then
            echo "❌ Требуется CentOS/RHEL 8 или новее"
            exit 1
        fi
        ;;
    *)
        echo "❌ Неподдерживаемая ОС: $OS"
        echo "Поддерживаются: Ubuntu 20.04+, Debian 11+, CentOS 8+"
        exit 1
        ;;
esac

# Проверка ресурсов сервера
echo ""
echo "🔍 Проверка ресурсов сервера..."

# RAM
RAM_GB=$(free -g | awk 'NR==2{printf "%.1f", $2}')
if (( $(echo "$RAM_GB < 3.5" | bc -l) )); then
    echo "⚠️  Внимание: RAM = ${RAM_GB}GB (рекомендуется 4GB+)"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ RAM: ${RAM_GB}GB"
fi

# Диск
DISK_GB=$(df -h / | awk 'NR==2{printf "%.1f", $4}')
if (( $(echo "$DISK_GB < 25" | bc -l) )); then
    echo "⚠️  Внимание: Свободно ${DISK_GB}GB (рекомендуется 40GB+)"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Диск: ${DISK_GB}GB свободно"
fi

# CPU
CPU_CORES=$(nproc)
if [[ $CPU_CORES -lt 2 ]]; then
    echo "⚠️  Внимание: CPU = ${CPU_CORES} ядер (рекомендуется 2+)"
else
    echo "✅ CPU: ${CPU_CORES} ядер"
fi

# Настройка переменных
echo ""
echo "⚙️  Настройка конфигурации..."

# Домен
read -p "🌐 Введите ваш домен (например: youinvest.duckdns.org): " DOMAIN
if [[ -z "$DOMAIN" ]]; then
    DOMAIN="youinvest.duckdns.org"
fi
echo "✅ Домен: $DOMAIN"

# Email для SSL
read -p "📧 Email для SSL сертификата: " SSL_EMAIL
if [[ -z "$SSL_EMAIL" ]]; then
    SSL_EMAIL="admin@$DOMAIN"
fi
echo "✅ Email: $SSL_EMAIL"

# Пароли
DB_PASSWORD=$(openssl rand -base64 32 | tr -d '/')
REDIS_PASSWORD=$(openssl rand -base64 16 | tr -d '/')
MINIO_PASSWORD=$(openssl rand -base64 24 | tr -d '/')
JWT_SECRET=$(openssl rand -base64 32 | tr -d '/')

echo "✅ Пароли сгенерированы"

# Обновление системы
echo ""
echo "📦 Обновление системы..."

case $OS in
    ubuntu|debian)
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -y
        apt-get upgrade -y
        apt-get install -y curl wget git ufw fail2ban htop nano bc
        ;;
    centos|rhel|rocky|almalinux)
        yum update -y
        yum install -y curl wget git firewalld fail2ban htop nano bc
        ;;
esac

echo "✅ Система обновлена"

# Установка Docker
echo ""
echo "🐳 Установка Docker..."

if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Docker Compose
    DOCKER_COMPOSE_VERSION="2.28.1"
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Запуск Docker
    systemctl enable docker
    systemctl start docker
    
    echo "✅ Docker установлен"
else
    echo "✅ Docker уже установлен"
fi

# Создание пользователя приложения
echo ""
echo "👤 Создание пользователя приложения..."

if ! id "youinvest" &>/dev/null; then
    useradd -m -s /bin/bash youinvest
    usermod -aG docker youinvest
    echo "✅ Пользователь youinvest создан"
else
    echo "✅ Пользователь youinvest уже существует"
fi

# Настройка firewall
echo ""
echo "🔥 Настройка firewall..."

case $OS in
    ubuntu|debian)
        ufw --force enable
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        echo "✅ UFW настроен"
        ;;
    centos|rhel|rocky|almalinux)
        systemctl enable firewalld
        systemctl start firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http  
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        echo "✅ Firewalld настроен"
        ;;
esac

# Создание директории проекта
echo ""
echo "📁 Создание структуры проекта..."

PROJECT_DIR="/opt/youinvest"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Создаем основные директории
mkdir -p {data/postgres,data/redis,data/minio,logs,ssl,backups}
chown -R youinvest:youinvest $PROJECT_DIR

echo "✅ Структура проекта создана"

# Создание docker-compose.prod.yml
echo ""
echo "🐳 Создание production конфигурации..."

cat > docker-compose.prod.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: youinvest-postgres
    environment:
      POSTGRES_DB: youinvest_prod
      POSTGRES_USER: youinvest_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./ssl:/ssl:ro
    networks:
      - youinvest-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U youinvest_user -d youinvest_prod"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: youinvest-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - ./data/redis:/data
    networks:
      - youinvest-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  minio:
    image: minio/minio:latest
    container_name: youinvest-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: youinvest-admin
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - ./data/minio:/data
    networks:
      - youinvest-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    image: youinvest/backend:latest
    container_name: youinvest-backend
    environment:
      ENVIRONMENT: production
      DEBUG: "false"
      APP_NAME: YouInvest
      
      # Database
      DATABASE_HOST: postgres
      DATABASE_PORT: 5432
      DATABASE_NAME: youinvest_prod
      DATABASE_USER: youinvest_user
      DATABASE_PASSWORD: ${DB_PASSWORD}
      
      # Redis
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      
      # MinIO
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: youinvest-admin
      MINIO_SECRET_KEY: ${MINIO_PASSWORD}
      MINIO_BUCKET_NAME: youinvest-files
      
      # Security
      SECRET_KEY: ${JWT_SECRET}
      JWT_SECRET_KEY: ${JWT_SECRET}
      ENCRYPTION_KEY: ${JWT_SECRET}
      
      # CORS
      CORS_ORIGINS: https://${DOMAIN},https://www.${DOMAIN}
      TRUSTED_HOSTS: ${DOMAIN},www.${DOMAIN}
      
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    networks:
      - youinvest-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: youinvest/frontend:latest
    container_name: youinvest-frontend
    environment:
      NEXT_PUBLIC_API_URL: https://${DOMAIN}/api
      NEXT_PUBLIC_APP_NAME: YouInvest
      NEXT_PUBLIC_APP_URL: https://${DOMAIN}
      NEXT_PUBLIC_ENVIRONMENT: production
    networks:
      - youinvest-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  traefik:
    image: traefik:v3.0
    container_name: youinvest-traefik
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${SSL_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./ssl:/letsencrypt
    networks:
      - youinvest-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(\`traefik.${DOMAIN}\`)"
      - "traefik.http.routers.dashboard.tls=true"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
      - "traefik.http.routers.dashboard.service=api@internal"

  # Мониторинг
  prometheus:
    image: prom/prometheus:latest
    container_name: youinvest-prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    networks:
      - youinvest-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: youinvest-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - ./data/grafana:/var/lib/grafana
    networks:
      - youinvest-network
    restart: unless-stopped

networks:
  youinvest-network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  minio_data:
  grafana_data:
EOF

echo "✅ Docker Compose конфигурация создана"

# Создание .env файла
cat > .env << EOF
# Production конфигурация YouInvest
ENVIRONMENT=production
DEBUG=false
APP_NAME=YouInvest
DOMAIN=${DOMAIN}

# Database
DATABASE_PASSWORD=${DB_PASSWORD}

# Redis  
REDIS_PASSWORD=${REDIS_PASSWORD}

# MinIO
MINIO_PASSWORD=${MINIO_PASSWORD}

# Security
JWT_SECRET=${JWT_SECRET}

# SSL
SSL_EMAIL=${SSL_EMAIL}
EOF

echo "✅ Переменные окружения настроены"

# Создание скрипта запуска
cat > start.sh << 'EOF'
#!/bin/bash

echo "🚀 Запуск YouInvest Production"
echo "============================="

# Загрузка переменных окружения
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Проверка Docker
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker не запущен"
    sudo systemctl start docker
    sleep 5
fi

# Создание сети если не существует
docker network ls | grep youinvest-network >/dev/null || docker network create youinvest-network

# Запуск сервисов
docker-compose -f docker-compose.prod.yml up -d

# Ожидание готовности
echo "⏳ Ожидание готовности сервисов..."
sleep 30

# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "🎉 YouInvest запущен!"
echo "===================="
echo ""
echo "🌐 Сайт: https://${DOMAIN}"
echo "📚 API:  https://${DOMAIN}/api/docs"
echo "📊 Мониторинг: https://traefik.${DOMAIN}"
echo ""
echo "Логи: docker-compose -f docker-compose.prod.yml logs -f"
EOF

chmod +x start.sh

# Создание скрипта остановки
cat > stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Остановка YouInvest..."
docker-compose -f docker-compose.prod.yml down
echo "✅ Остановлено"
EOF

chmod +x stop.sh

# Создание скрипта бэкапа
cat > backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/youinvest/backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "💾 Создание бэкапа..."

# Бэкап PostgreSQL
docker exec youinvest-postgres pg_dump -U youinvest_user youinvest_prod > "$BACKUP_DIR/db_backup_$DATE.sql"

# Бэкап конфигурации
tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" docker-compose.prod.yml .env

# Удаление старых бэкапов (старше 7 дней)
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete

echo "✅ Бэкап создан: $DATE"
EOF

chmod +x backup.sh

# Создание systemd сервиса
cat > /etc/systemd/system/youinvest.service << EOF
[Unit]
Description=YouInvest Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/youinvest
ExecStart=/opt/youinvest/start.sh
ExecStop=/opt/youinvest/stop.sh
TimeoutStartSec=0
User=youinvest

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable youinvest

# Настройка cron для бэкапов
(crontab -u youinvest -l 2>/dev/null; echo "0 2 * * * /opt/youinvest/backup.sh") | crontab -u youinvest -

echo "✅ Автозапуск и бэкапы настроены"

# Установка права доступа
chown -R youinvest:youinvest $PROJECT_DIR
chmod +x $PROJECT_DIR/*.sh

echo ""
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo "======================"
echo ""
echo "📋 Что дальше:"
echo ""
echo "1. Настройте DNS для домена $DOMAIN на IP: $(curl -s ifconfig.me)"
echo "2. Запустите сервис: sudo systemctl start youinvest"
echo "3. Проверьте статус: sudo systemctl status youinvest"
echo ""
echo "🌐 После настройки DNS сайт будет доступен:"
echo "   https://$DOMAIN"
echo ""
echo "📊 Управление сервисом:"
echo "   sudo systemctl start youinvest   # Запуск"
echo "   sudo systemctl stop youinvest    # Остановка"
echo "   sudo systemctl restart youinvest # Перезапуск"
echo ""
echo "📋 Логи:"
echo "   cd /opt/youinvest"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "💾 Бэкап (автоматически каждый день в 2:00):"
echo "   /opt/youinvest/backup.sh"
echo ""
echo "✅ Готово к использованию!"
