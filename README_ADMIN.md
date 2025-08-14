# Admin Panel (Dohodometr)

## Домены
- Frontend: https://admin.dohodometr.ru
- Backend: https://api.dohodometr.ru

## Быстрый запуск (VPS)
1) DNS на VPS
2) Правьте IP-allowlist в deploy/nginx/admin.conf
3) ENV:
- DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/dohodometr
- ADMIN_TOKEN=<секрет>
- RUN_SCHEDULER=true
- CORS_ORIGINS=["https://admin.dohodometr.ru"]
- DB_SCHEMA=admin
- REPO=<owner/repo>, GH_TOKEN (опц.)

4) Запуск: docker compose -f docker-compose.admin.yml up -d --build

## CI/CD
- .github/workflows/admin-ci.yml — линты/тесты
- .github/workflows/admin-deploy.yml — деплой по SSH
