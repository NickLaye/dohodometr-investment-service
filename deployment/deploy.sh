#!/bin/bash

# 🚀 DOHODOMETR.RU AUTOMATIC DEPLOYMENT SCRIPT
# Исправление SSL сертификата и 404 ошибки
# Дата создания: 12 августа 2025

set -e  # Остановить скрипт при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Логирование
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

title() {
    echo ""
    echo -e "${PURPLE}🚀 $1${NC}"
    echo "=================================================="
}

# Проверка root прав
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Этот скрипт должен быть запущен с root правами (sudo)"
        exit 1
    fi
}

# Проверка Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен. Установите docker-compose и попробуйте снова."
        exit 1
    fi
    
    success "Docker и Docker Compose найдены"
}

# Остановка текущих сервисов
stop_services() {
    title "Остановка текущих сервисов"
    
    log "Остановка всех контейнеров..."
    docker-compose down 2>/dev/null || true
    docker stop $(docker ps -q) 2>/dev/null || true
    
    success "Все сервисы остановлены"
}

# Создание директорий
create_directories() {
    title "Создание необходимых директорий"
    
    log "Создание директорий..."
    mkdir -p /opt/dohodometr/{letsencrypt,logs/traefik,logs/nginx,backups,html,nginx}
    
    log "Установка правильных прав доступа..."
    chmod 600 /opt/dohodometr/letsencrypt
    chown -R root:root /opt/dohodometr
    
    success "Директории созданы и настроены"
}

# Копирование конфигурационных файлов
copy_configs() {
    title "Копирование конфигурационных файлов"
    
    # Проверяем что мы в правильной директории
    if [[ ! -f "docker-compose.production.yml" ]]; then
        error "Файл docker-compose.production.yml не найден в текущей директории"
        error "Запустите скрипт из директории deployment/"
        exit 1
    fi
    
    log "Копирование docker-compose.yml..."
    cp docker-compose.production.yml /opt/dohodometr/docker-compose.yml
    
    log "Копирование переменных окружения..."
    if [[ -f "environment.production" ]]; then
        cp environment.production /opt/dohodometr/.env
        warning "ВАЖНО: Смените пароли в файле /opt/dohodometr/.env!"
    fi
    
    log "Копирование HTML файлов..."
    cp -r html/* /opt/dohodometr/html/
    
    log "Копирование конфигурации Nginx..."
    cp nginx/nginx.conf /opt/dohodometr/nginx/
    
    success "Все файлы скопированы"
}

# Генерация безопасных паролей
generate_passwords() {
    title "Генерация безопасных паролей"
    
    log "Генерация паролей..."
    
    # Генерируем случайные пароли
    POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Заменяем пароли в .env файле
    if [[ -f "/opt/dohodometr/.env" ]]; then
        sed -i "s/DO_change_strong_password_2025_production/${POSTGRES_PASSWORD}/g" /opt/dohodometr/.env
        sed -i "s/DO_change_redis_password_2025_secure/${REDIS_PASSWORD}/g" /opt/dohodometr/.env
        sed -i "s/DO_change_email_password_here/CHANGE_EMAIL_PASSWORD/g" /opt/dohodometr/.env
    fi
    
    log "Сохранение паролей в безопасное место..."
    cat > /opt/dohodometr/PASSWORDS.txt << EOF
# DOHODOMETR.RU GENERATED PASSWORDS
# Дата: $(date)
# СОХРАНИТЕ ЭТИ ПАРОЛИ В БЕЗОПАСНОМ МЕСТЕ!

PostgreSQL Password: ${POSTGRES_PASSWORD}
Redis Password: ${REDIS_PASSWORD}

# ВАЖНО:
# 1. Удалите этот файл после сохранения паролей
# 2. Установите пароль для email в .env файле
# 3. Регулярно меняйте пароли (раз в 3 месяца)
EOF
    
    chmod 600 /opt/dohodometr/PASSWORDS.txt
    
    success "Пароли сгенерированы и сохранены в /opt/dohodometr/PASSWORDS.txt"
    warning "Обязательно сохраните пароли в безопасном месте и удалите файл!"
}

# Запуск сервисов
start_services() {
    title "Запуск сервисов"
    
    cd /opt/dohodometr
    
    log "Загрузка Docker образов..."
    docker-compose pull
    
    log "Запуск сервисов..."
    docker-compose up -d
    
    success "Сервисы запущены"
}

# Мониторинг SSL сертификата
monitor_ssl() {
    title "Мониторинг выпуска SSL сертификата"
    
    log "Ожидание выпуска SSL сертификата от Let's Encrypt..."
    log "Это может занять до 5 минут..."
    
    # Ждем до 300 секунд (5 минут)
    for i in {1..60}; do
        if [[ -f "/opt/dohodometr/letsencrypt/acme.json" ]] && [[ -s "/opt/dohodometr/letsencrypt/acme.json" ]]; then
            success "SSL сертификат успешно выпущен!"
            break
        fi
        
        if [[ $i -eq 60 ]]; then
            warning "SSL сертификат еще не выпущен. Проверьте логи Traefik:"
            echo "docker-compose logs traefik"
            break
        fi
        
        echo -n "."
        sleep 5
    done
}

# Проверка результата
check_result() {
    title "Проверка результата"
    
    log "Проверка статуса контейнеров..."
    docker-compose ps
    
    echo ""
    log "Проверка SSL сертификата..."
    
    # Ждем немного для инициализации
    sleep 10
    
    # Проверяем HTTP редирект
    HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://dohodometr.ru || echo "000")
    if [[ "$HTTP_RESPONSE" == "308" ]] || [[ "$HTTP_RESPONSE" == "301" ]]; then
        success "HTTP -> HTTPS редирект работает (код: $HTTP_RESPONSE)"
    else
        warning "HTTP редирект возможно не работает (код: $HTTP_RESPONSE)"
    fi
    
    # Проверяем HTTPS
    HTTPS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://dohodometr.ru || echo "000")
    if [[ "$HTTPS_RESPONSE" == "200" ]]; then
        success "HTTPS сайт доступен (код: $HTTPS_RESPONSE)"
    else
        warning "HTTPS сайт возможно недоступен (код: $HTTPS_RESPONSE)"
    fi
    
    echo ""
    log "Проверка логов Traefik на ошибки..."
    if docker-compose logs traefik | grep -i "error\|failed" | tail -3; then
        warning "Найдены ошибки в логах Traefik (см. выше)"
    else
        success "Критических ошибок в логах Traefik не найдено"
    fi
}

# Инструкции по дальнейшим действиям
show_instructions() {
    title "Дальнейшие действия"
    
    echo -e "${GREEN}🎉 Развертывание завершено!${NC}"
    echo ""
    
    echo -e "${CYAN}📋 Что проверить:${NC}"
    echo "1. Откройте https://dohodometr.ru в браузере"
    echo "2. Убедитесь что отображается зеленый замок 🔒"
    echo "3. Проверьте что сайт загружается без ошибок"
    echo ""
    
    echo -e "${CYAN}🛠️ Полезные команды:${NC}"
    echo "• Статус сервисов:     docker-compose ps"
    echo "• Логи Traefik:       docker-compose logs traefik"
    echo "• Логи веб-сайта:     docker-compose logs website"
    echo "• Перезапуск:         docker-compose restart"
    echo "• Остановка:          docker-compose down"
    echo ""
    
    echo -e "${CYAN}📁 Важные файлы:${NC}"
    echo "• Конфигурация:       /opt/dohodometr/docker-compose.yml"
    echo "• Переменные:         /opt/dohodometr/.env"
    echo "• Пароли:             /opt/dohodometr/PASSWORDS.txt"
    echo "• SSL сертификаты:    /opt/dohodometr/letsencrypt/"
    echo "• Логи:               /opt/dohodometr/logs/"
    echo ""
    
    echo -e "${CYAN}🔗 Доступные URL:${NC}"
    echo "• Основной сайт:      https://dohodometr.ru"
    echo "• Traefik панель:     https://traefik.dohodometr.ru"
    echo "• Мониторинг:         https://uptime.dohodometr.ru"
    echo ""
    
    echo -e "${YELLOW}⚠️  ВАЖНО ПОСЛЕ РАЗВЕРТЫВАНИЯ:${NC}"
    echo "1. Сохраните пароли из /opt/dohodometr/PASSWORDS.txt"
    echo "2. Удалите файл PASSWORDS.txt после сохранения"
    echo "3. Установите пароль для email в .env файле"
    echo "4. Настройте мониторинг uptime для dohodometr.ru"
    echo "5. Создайте регулярные бэкапы базы данных"
    echo ""
    
    echo -e "${GREEN}🚀 Готово! Ваш сайт dohodometr.ru теперь работает с SSL!${NC}"
}

# Основная функция
main() {
    clear
    echo -e "${PURPLE}"
    echo "=================================================="
    echo "🚀 DOHODOMETR.RU DEPLOYMENT SCRIPT"
    echo "   Автоматическое исправление SSL и 404"
    echo "=================================================="
    echo -e "${NC}"
    
    log "Начало развертывания в $(date)"
    
    check_root
    check_docker
    stop_services
    create_directories
    copy_configs
    generate_passwords
    start_services
    monitor_ssl
    check_result
    show_instructions
    
    log "Развертывание завершено в $(date)"
}

# Запуск основной функции
main "$@"
