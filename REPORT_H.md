# REPORT_H — Инфра/деплой (zero-downtime) и секреты

## 1) Среды и конфигурация

- `deployment/docker-compose.production.yml` (Traefik + backend + frontend + Postgres + Redis + Uptime). Переменные — через `environment.production`/секреты.
- `cd-production-fixed.yml` — build & push → image scan → SSH deploy на сервер, health-check, prune.

## 2) Zero-downtime

- `docker compose up -d --no-deps backend frontend` — rolling на уровне контейнеров, Traefik снимает трафик при неуспешном health.
- Бэкап БД перед деплоем: подключено.

## 3) Секреты

- Не коммитятся; используются `secrets.*` в Actions и `.env` на сервере.
- Рекомендация: хранить prod переменные в GitHub Environments и на сервере в `.env` с ограничениями прав.

## 4) DNS/TLS

- Traefik c Let's Encrypt; HSTS включен; редирект HTTP→HTTPS.

## 5) Риски/улучшения

- Можно добавить canary (второй сервис backend-v2 + Traefik service weights) — для пошаговой выкладки.
- Авто-rollback: в SSH-скрипт добавить проверку метрик/логов и откат образов по предыдущему тегу, если health не проходит в N секунд.

## 6) Скрипты

- В `deployment/` уже есть `deploy.sh`, `generate_secure_env.sh`, `restart_services.sh`. Проверки и инструкции в `README_DEPLOY.md`.
