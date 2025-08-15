# Тестовое окружение и фикстуры

## ENV для тестов
- В `backend/conftest.py` форсируется `ENVIRONMENT=development` для юнит‑тестов и безопасные значения `DATABASE_URL` (SQLite) и `REDIS_URL`.
- Интеграционные тесты в CI используют Postgres/Redis сервисы и `ENVIRONMENT=testing`.

## Сброс БД между тестами
- Для sync‑движка: внутри фикстуры `db_session` выполняется `Base.drop_all()` → `Base.create_all()` на памяти (`sqlite+pysqlite:///:memory:`) с `StaticPool`, обеспечивая чистое состояние.
- Для async‑движка: фикстура `async_db_session` создаёт схемы на `sqlite+aiosqlite:///:memory:` и закрывает их после теста.

## Клиенты
- `client`: `fastapi.TestClient` с переопределением `get_db` на сессию тестовой БД.
- `async_client`: `httpx.AsyncClient` с переопределением `get_db` на асинхронную сессию.

## Аутентификация
- `auth_headers`: создаёт пользователя в БД (если не найден) и возвращает заголовок `Authorization: Bearer <jwt>` на его ID.
- `superuser_headers`: генерирует JWT с признаком суперпользователя.

## Прочее
- Доп. мок‑фикстуры: `mock_redis`, `mock_celery`, `mock_email_service`.
- Данные для тестов: `sample_portfolio`, `sample_account`, `sample_transaction`, `sample_instrument`.

## Быстрый старт локально
- Установить окружение: `make backend-init` и `make fe-init`.
- Запустить быстрые бэкенд‑тесты: `make backend-test-fast`.
- Прогнать фронт‑юнит: `make fe-test`.
- Сводка качества: `make quality-gate` (артефакты в `reports/`).
