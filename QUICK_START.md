# 🚀 Быстрый запуск локально

## Предварительные требования

1. **Docker Desktop** - [Скачать](https://www.docker.com/products/docker-desktop/)
2. **Git** - для клонирования репозитория

## Шаг 1: Подготовка

```bash
# Клонируйте репозиторий (если еще не сделали)
git clone <your-repo-url>
cd investment-service

# Создайте .env файл из шаблона
cp env.example .env
```

## Шаг 2: Запуск

### Автоматический запуск (рекомендуется)

**На macOS/Linux:**
```bash
./start_dev.sh
```

**На Windows:**
```cmd
start_dev.bat
```

### Ручной запуск

```bash
# Создайте необходимые директории
mkdir -p data/postgres data/redis data/minio logs

# Запустите сервисы
docker-compose -f docker-compose.dev.yml up --build -d

# Проверьте статус
docker-compose -f docker-compose.dev.yml ps
```

## Шаг 3: Проверка работы

После запуска откройте в браузере:

- **🌐 Приложение**: http://localhost:3000
- **🔧 API**: http://localhost:8000  
- **📚 Документация API**: http://localhost:8000/docs
- **🗄️ MinIO (S3)**: http://localhost:9001 (admin/admin123)
- **📊 Grafana**: http://localhost:3001 (admin/admin)

## Шаг 4: Создание первого пользователя

1. Откройте http://localhost:3000
2. Нажмите "Создать аккаунт"
3. Зарегистрируйтесь с вашими данными
4. Войдите в систему

## Полезные команды

```bash
# Просмотр логов
docker-compose -f docker-compose.dev.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend

# Остановка сервисов
docker-compose -f docker-compose.dev.yml down

# Перезапуск
docker-compose -f docker-compose.dev.yml restart

# Полная очистка (удаление контейнеров и данных)
docker-compose -f docker-compose.dev.yml down -v
```

## Проверка готовности сервисов

Из директории `backend/`:

```bash
cd backend
python check_startup.py
```

## Возможные проблемы

### Порты заняты
Если порты 3000, 8000, 5432 уже заняты, измените их в `docker-compose.dev.yml`:

```yaml
# Пример изменения портов
ports:
  - "3001:3000"  # frontend
  - "8001:8000"  # backend
  - "5433:5432"  # postgres
```

### Медленный запуск
Первый запуск может занять 5-10 минут для скачивания образов и сборки.

### Ошибки базы данных
Если есть ошибки подключения к PostgreSQL:

```bash
# Проверьте статус контейнера
docker-compose -f docker-compose.dev.yml ps

# Перезапустите только базу данных
docker-compose -f docker-compose.dev.yml restart postgres

# Посмотрите логи
docker-compose -f docker-compose.dev.yml logs postgres
```

## Следующие шаги

1. **Создайте портфель** в интерфейсе
2. **Добавьте счет** брокера
3. **Загрузите CSV отчет** для тестирования импорта
4. **Изучите аналитику** на дашборде

---

🆘 **Нужна помощь?** Создайте issue в репозитории или напишите в поддержку.
