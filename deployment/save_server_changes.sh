#!/bin/bash

# ========================================================
# 🚨 СОХРАНЕНИЕ ИЗМЕНЕНИЙ С СЕРВЕРА ПЕРЕД GIT DEPLOY
# ========================================================
# Скрипт для сохранения изменений, внесенных напрямую на сервере
# Автор: Dohodometr Team
# Дата: 13 августа 2025

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}========================================================${NC}"
echo -e "${RED}🚨 СОХРАНЕНИЕ ИЗМЕНЕНИЙ С СЕРВЕРА${NC}"
echo -e "${RED}========================================================${NC}"

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Этот скрипт должен запускаться с правами root${NC}"
   exit 1
fi

# Переменные
SERVER_DIR="/opt/dohodometr"
BACKUP_NAME="server_changes_$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="/opt/${BACKUP_NAME}.tar.gz"

echo -e "${YELLOW}📍 Сервер директория: $SERVER_DIR${NC}"
echo -e "${YELLOW}💾 Файл бэкапа: $BACKUP_FILE${NC}"
echo ""

# Проверка существования директории
if [ ! -d "$SERVER_DIR" ]; then
    echo -e "${RED}❌ Директория $SERVER_DIR не существует${NC}"
    exit 1
fi

cd "$SERVER_DIR"

echo -e "${BLUE}🔍 АНАЛИЗ ИЗМЕНЕНИЙ НА СЕРВЕРЕ:${NC}"
echo ""

# Проверка git статуса
if [ -d ".git" ]; then
    echo -e "${YELLOW}📊 Git статус:${NC}"
    git status --porcelain | head -10
    echo ""
    
    echo -e "${YELLOW}📈 Последние коммиты:${NC}"
    git log --oneline -5
    echo ""
    
    echo -e "${YELLOW}🔧 Измененные файлы за последние 24 часа:${NC}"
    git diff --name-only HEAD~1 2>/dev/null | head -10 || echo "Нет git истории"
    echo ""
fi

# Поиск недавно измененных файлов
echo -e "${YELLOW}📁 Файлы, измененные за последние 24 часа:${NC}"
find . -type f -mtime -1 -name "*.py" | head -15
echo ""

# Проверка важных файлов
echo -e "${YELLOW}🗂️  Проверка ключевых файлов:${NC}"

# Модели
if [ -d "backend/app/models" ]; then
    echo -e "${BLUE}   Модели БД:${NC}"
    ls -la backend/app/models/*.py | awk '{print "     " $9 " (" $6 " " $7 " " $8 ")"}'
fi

# База данных
if [ -f "backend/app/core/database.py" ]; then
    echo -e "${BLUE}   database.py: $(stat -c %y backend/app/core/database.py)${NC}"
fi

if [ -f "backend/app/core/database_sync.py" ]; then
    echo -e "${BLUE}   database_sync.py: $(stat -c %y backend/app/core/database_sync.py)${NC}"
fi

# Миграции
if [ -d "backend/migrations/versions" ]; then
    echo -e "${BLUE}   Последние миграции:${NC}"
    ls -la backend/migrations/versions/ | tail -3 | awk '{print "     " $9 " (" $6 " " $7 " " $8 ")"}'
fi

echo ""

# Создание полного бэкапа
echo -e "${YELLOW}📦 Создаем полный бэкап сервера...${NC}"

# Исключаем временные файлы и логи
tar -czf "$BACKUP_FILE" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='logs/*' \
    --exclude='letsencrypt/*' \
    --exclude='postgres_data' \
    --exclude='redis_data' \
    backend/ frontend/ deployment/ 

# Добавляем конфигурационные файлы отдельно
if [ -f ".env" ]; then
    tar -rf "${BACKUP_FILE%.gz}" .env
    gzip -f "${BACKUP_FILE%.gz}"
fi

if [ -f "docker-compose.production.yml" ]; then
    tar -rf "${BACKUP_FILE%.gz}" docker-compose.production.yml 2>/dev/null || true
    gzip -f "${BACKUP_FILE%.gz}" 2>/dev/null || true
fi

echo -e "${GREEN}✅ Бэкап создан: $BACKUP_FILE${NC}"

# Информация о бэкапе
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo -e "${GREEN}📊 Размер бэкапа: $BACKUP_SIZE${NC}"

# Создание детального отчета
REPORT_FILE="/opt/${BACKUP_NAME}_report.txt"
cat > "$REPORT_FILE" << EOF
========================================================
DOHODOMETR.RU - ОТЧЕТ ОБ ИЗМЕНЕНИЯХ НА СЕРВЕРЕ
========================================================
Дата: $(date)
Сервер: $(hostname)
Директория: $SERVER_DIR
Бэкап: $BACKUP_FILE

СТАТИСТИКА:
-----------
Размер бэкапа: $BACKUP_SIZE
Файлы в бэкапе: $(tar -tzf "$BACKUP_FILE" | wc -l)

НЕДАВНО ИЗМЕНЕННЫЕ ФАЙЛЫ:
-------------------------
$(find $SERVER_DIR -type f -mtime -1 -name "*.py" 2>/dev/null | head -20)

GIT СТАТУС:
-----------
$(cd $SERVER_DIR && git status 2>/dev/null || echo "Git не инициализирован")

СТРУКТУРА БД:
-------------
$(docker-compose exec -T postgres psql -U postgres -d dohodometr -c "\dt" 2>/dev/null | head -20 || echo "БД недоступна")

АКТИВНЫЕ КОНТЕЙНЕРЫ:
--------------------
$(docker-compose ps 2>/dev/null || echo "Docker Compose не запущен")

ИНСТРУКЦИИ:
-----------
1. Скачайте бэкап на локальную машину:
   scp root@$(hostname -I | awk '{print $1}'):$BACKUP_FILE ./

2. Распакуйте и проверьте изменения:
   tar -xzf $(basename $BACKUP_FILE)

3. Интегрируйте изменения в локальный код

4. Протестируйте локально

5. Закоммитьте в git и задеплойте

ВНИМАНИЕ: НЕ ЗАПУСКАЙТЕ git deploy без интеграции этих изменений!
EOF

echo -e "${GREEN}📋 Отчет создан: $REPORT_FILE${NC}"

echo ""
echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}✅ ИЗМЕНЕНИЯ СОХРАНЕНЫ!${NC}"
echo -e "${GREEN}========================================================${NC}"
echo ""
echo -e "${BLUE}📋 СЛЕДУЮЩИЕ ШАГИ:${NC}"
echo ""
echo -e "${BLUE}1. На локальной машине скачайте бэкап:${NC}"
echo -e "${BLUE}   scp root@$(hostname -I | awk '{print $1}'):$BACKUP_FILE ./${NC}"
echo -e "${BLUE}   scp root@$(hostname -I | awk '{print $1}'):$REPORT_FILE ./${NC}"
echo ""
echo -e "${BLUE}2. Распакуйте и проверьте:${NC}"
echo -e "${BLUE}   tar -xzf $(basename $BACKUP_FILE)${NC}"
echo -e "${BLUE}   cat $(basename $REPORT_FILE)${NC}"
echo ""
echo -e "${BLUE}3. Интегрируйте изменения в git${NC}"
echo ""
echo -e "${BLUE}4. Только потом запускайте git deploy${NC}"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО: Эти файлы содержат изменения, которые БУДУТ ПОТЕРЯНЫ при git deploy!${NC}"
echo ""
echo -e "${GREEN}🔐 Файлы готовы к скачиванию:${NC}"
echo -e "${GREEN}   $BACKUP_FILE${NC}"
echo -e "${GREEN}   $REPORT_FILE${NC}"
