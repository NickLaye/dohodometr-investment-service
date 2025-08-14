# REPORT_I — Наблюдаемость, перфоманс, DR

## 1) SLO/SLI

- Базовые метрики Prometheus есть (requests, duration, active connections).
- Предложение SLO: uptime 99.9%, p95 API < 300ms, error-rate < 1%.

## 2) Метрики/трейсы

- Prometheus + алерты в `infra/prometheus/alerts.yml`. Предложение: добавить экспортеры БД/Redis, и интеграцию Sentry (SDK уже подключается при наличии DSN).

## 3) Эндпоинты

- `/health`, `/ready`, `/live`, `/metrics` — реализованы.

## 4) Бэкапы/DR

- В CD есть бэкап перед деплоем. Рекомендация: nightly cron, ротация, тест восстановления на staging раз в N дней.

## 5) Перфоманс тесты

- В `requirements-dev.txt` есть `locust`; добавить профили baseline/stress/soak по готовности.

## 6) FE перфоманс/SEO

- Добавить проверку Core Web Vitals (инструменты Lighthouse/Pagespeed в отдельном workflow) и sitemap/robots проверку.
