#!/bin/bash

# Скрипт для проверки здоровья запущенных сервисов

set -e

echo "🔍 Проверка здоровья сервисов"
echo "==============================="

# Функция для проверки HTTP эндпоинта
check_http() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        echo "✅ $name: OK"
        return 0
    else
        echo "❌ $name: недоступен ($url)"
        return 1
    fi
}

# Функция для проверки статуса Docker контейнера
check_container() {
    local container_name=$1
    local service_name=$2
    
    if docker-compose -f docker-compose.dev.yml ps | grep "$container_name" | grep -q "Up"; then
        echo "✅ $service_name: контейнер запущен"
        return 0
    else
        echo "❌ $service_name: контейнер не запущен"
        return 1
    fi
}

echo "📦 Проверка Docker контейнеров:"
echo "--------------------------------"

# Проверяем статус контейнеров
check_container "postgres" "PostgreSQL"
check_container "redis" "Redis"
check_container "minio" "MinIO"
check_container "backend" "Backend API"
check_container "frontend" "Frontend"

echo ""
echo "🌐 Проверка HTTP сервисов:"
echo "---------------------------"

# Ждем немного, чтобы сервисы успели запуститься
sleep 2

# Проверяем HTTP эндпоинты
check_http "http://localhost:3000" "Frontend"
check_http "http://localhost:8000/health" "Backend Health" "200"
check_http "http://localhost:8000/docs" "API Documentation"
check_http "http://localhost:9001/minio/health/live" "MinIO Health"

echo ""
echo "🗄️  Проверка подключений к базам данных:"
echo "-----------------------------------------"

# Проверяем подключение к PostgreSQL
if docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready >/dev/null 2>&1; then
    echo "✅ PostgreSQL: принимает подключения"
else
    echo "❌ PostgreSQL: не принимает подключения"
fi

# Проверяем подключение к Redis
if docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis: отвечает на ping"
else
    echo "❌ Redis: не отвечает на ping"
fi

echo ""
echo "📊 Использование ресурсов:"
echo "---------------------------"

# Показываем использование ресурсов
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep -E "(CONTAINER|postgres|redis|minio|backend|frontend)"

echo ""
echo "📋 Полезные ссылки:"
echo "-------------------"
echo "🌐 Приложение:     http://localhost:3000"
echo "🔧 Backend API:    http://localhost:8000"
echo "📚 API Docs:       http://localhost:8000/docs"
echo "🗄️  MinIO Console:  http://localhost:9001"
echo "📊 Grafana:        http://localhost:3001"

echo ""
echo "✅ Проверка завершена!"
