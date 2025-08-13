#!/bin/bash

# Скрипт для запуска сервиса в development режиме

set -e

echo "🚀 Запуск сервиса учета инвестиций в DEV режиме"
echo "================================================"

# Проверяем, что Docker запущен
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker не запущен. Запустите Docker Desktop и повторите попытку."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "📝 Создаем .env файл из шаблона..."
    cp env.example .env
    echo "✅ Файл .env создан. Отредактируйте его при необходимости."
fi

# Создаем необходимые директории
echo "📁 Создаем директории..."
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/minio
mkdir -p logs

echo "🔧 Останавливаем предыдущие контейнеры..."
docker-compose -f docker-compose.dev.yml down --remove-orphans

echo "🏗️  Собираем и запускаем сервисы..."
docker-compose -f docker-compose.dev.yml up --build -d

echo "⏳ Ждем готовности сервисов..."
sleep 10

echo "🔍 Проверяем статус сервисов..."
docker-compose -f docker-compose.dev.yml ps

echo "✅ Сервисы запущены!"
echo ""
echo "📋 Доступные сервисы:"
echo "  🌐 Frontend:  http://localhost:3000"
echo "  🔧 Backend:   http://localhost:8000"
echo "  📚 API Docs:  http://localhost:8000/docs"
echo "  🗄️  MinIO:     http://localhost:9001 (admin/admin123)"
echo "  📊 Grafana:   http://localhost:3001 (admin/admin)"
echo ""
echo "📖 Логи можно посмотреть командой:"
echo "   docker-compose -f docker-compose.dev.yml logs -f [service_name]"
echo ""
echo "🛑 Для остановки используйте:"
echo "   docker-compose -f docker-compose.dev.yml down"
