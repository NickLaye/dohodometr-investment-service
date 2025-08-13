#!/bin/bash

# 🔄 Скрипт синхронизации очищенного кода на сервере
# Используйте этот скрипт для обновления кода на сервере после очистки

echo "🔄 СИНХРОНИЗАЦИЯ ОЧИЩЕННОГО КОДА"
echo "================================"

# Переходим в рабочую директорию
cd /opt/dohodometr || exit 1

# Создаем бэкап текущего состояния
echo "📦 Создаем бэкап..."
tar -czf "/opt/backup_before_cleanup_$(date +%Y%m%d_%H%M%S).tar.gz" \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='logs' \
    --exclude='letsencrypt' \
    . 2>/dev/null

# Обновляем код из GitHub
echo "📥 Получаем обновления из GitHub..."
git fetch origin main
git reset --hard origin/main

# Очищаем локальные временные файлы если остались
echo "🧹 Финальная очистка..."
find . -name ".DS_Store" -type f -delete 2>/dev/null || true
find . -name "._*" -type f -delete 2>/dev/null || true
rm -rf server_backup/ server_changes_*.tar.gz dohodometr_code.tar.gz 2>/dev/null || true

# Пересобираем только измененные сервисы
echo "🔄 Пересборка сервисов..."
cd deployment
docker-compose -f docker-compose.production.yml build --no-cache

# Проверяем статус
echo "✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА"
echo "=========================="
echo "Размер проекта: $(du -sh /opt/dohodometr | cut -f1)"
echo "Статус git: $(git log -1 --oneline)"
echo ""
echo "🚀 Для запуска обновленных сервисов:"
echo "docker-compose -f docker-compose.production.yml up -d"
