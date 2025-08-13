#!/bin/bash

# 🚀 БЫСТРЫЙ ДЕПЛОЙ DOHODOMETR.RU
# Дата: 12 августа 2025
# Статус: HTML Landing Page версия

echo "=== 🚀 БЫСТРЫЙ ДЕПЛОЙ DOHODOMETR.RU ==="
echo ""

# 1. Копируем все файлы на сервер
echo "📦 Копируем файлы деплоя на сервер..."
scp -r deployment/ root@185.23.35.41:/opt/dohodometr-deploy/

# 2. Подключаемся к серверу и запускаем деплой
echo "🌐 Подключаемся к серверу для деплоя..."
ssh root@185.23.35.41 << 'ENDSSH'

# Переходим в директорию деплоя
cd /opt/dohodometr-deploy/deployment

# Делаем скрипт исполняемым
chmod +x deploy.sh

# Запускаем автоматический деплой
echo "🚀 Запускаем деплой..."
./deploy.sh

# Проверяем результат
echo "✅ Проверяем статус..."
docker-compose ps

echo ""
echo "🎉 ДЕПЛОЙ ЗАВЕРШЕН!"
echo "🌐 Проверьте: https://dohodometr.ru"
echo "📊 SSL: https://www.ssllabs.com/ssltest/analyze.html?d=dohodometr.ru"

ENDSSH

echo ""
echo "✅ ДЕПЛОЙ КОМАНДЫ ВЫПОЛНЕНЫ!"
echo "🌐 Ваш сайт должен быть доступен на https://dohodometr.ru"
