# REPORT_G — Секьюрити приложения и заголовки

## 1) Заголовки и защита

- Backend (`app/main.py`) уже ставит:
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Permissions-Policy` (geolocation,camera,microphone,payment = ()), `CSP: default-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'`.
  - `HSTS` при https-схеме.
- Traefik dynamic (`infra/traefik/dynamic.yml`) дублирует security headers и rate-limit.

## 2) Аутентификация/сессии

- JWT access/refresh присутствует; алгоритм HS512 фиксирован (algorithm confusion mitigation).
- Добавлена инициализация Redis-blacklist токенов на старте (`init_token_blacklist` в `app/main.py`) для поддержки `logout`/ревокации.
- 2FA через TOTP с QR, бэкап коды на включение.

## 3) Валидация и защита API

- CORS/TrustedHost настроены через `settings`.
- Лимиты (slowapi) подключены; метрики Prometheus есть.

## 4) Шифрование

- Поля с шифрованием через Fernet с KDF PBKDF2HMAC (salt из `ENCRYPTION_SALT`).

## 5) Логи/аудит

- `log_security_event` используется на входе/2FA/выходе.
- Формат JSON логов включается через `setup_logging()` (см. `app/core/logging.py`).

## 6) Риски/рекомендации

- Убедиться, что в prod заданы сильные `SECRET_KEY`, `JWT_SECRET_KEY`, `ENCRYPTION_SALT`, пароли DB/MinIO (валидируется в `config.py`).
- Перекрыть CORS до точных прод-доменов в `ENV`.
- По готовности — включить `VIRUS_SCAN_ENABLED` и интеграцию с антивирусом при загрузке файлов.

## 7) Изменения

- Инициализация Redis blacklist токенов добавлена в `app/main.py` (не блокирует старт при отсутствии Redis).
