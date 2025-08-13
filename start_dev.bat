@echo off
chcp 65001 >nul

echo 🚀 Запуск сервиса учета инвестиций в DEV режиме
echo ================================================

REM Проверяем наличие .env файла
if not exist .env (
    echo 📝 Создаем .env файл из шаблона...
    copy env.example .env
    echo ✅ Файл .env создан. Отредактируйте его при необходимости.
)

REM Создаем необходимые директории
echo 📁 Создаем директории...
if not exist data mkdir data
if not exist data\postgres mkdir data\postgres
if not exist data\redis mkdir data\redis
if not exist data\minio mkdir data\minio
if not exist logs mkdir logs

echo 🔧 Останавливаем предыдущие контейнеры...
docker-compose -f docker-compose.dev.yml down --remove-orphans

echo 🏗️  Собираем и запускаем сервисы...
docker-compose -f docker-compose.dev.yml up --build -d

echo ⏳ Ждем готовности сервисов...
timeout /t 10 /nobreak >nul

echo 🔍 Проверяем статус сервисов...
docker-compose -f docker-compose.dev.yml ps

echo ✅ Сервисы запущены!
echo.
echo 📋 Доступные сервисы:
echo   🌐 Frontend:  http://localhost:3000
echo   🔧 Backend:   http://localhost:8000
echo   📚 API Docs:  http://localhost:8000/docs
echo   🗄️  MinIO:     http://localhost:9001 (admin/admin123)
echo   📊 Grafana:   http://localhost:3001 (admin/admin)
echo.
echo 📖 Логи можно посмотреть командой:
echo    docker-compose -f docker-compose.dev.yml logs -f [service_name]
echo.
echo 🛑 Для остановки используйте:
echo    docker-compose -f docker-compose.dev.yml down

pause
