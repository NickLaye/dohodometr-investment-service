# NEXT TASKS (repo-hardening)

- [BLOCKER] Branch protection — запустить вручную все 5 job.id через Actions (`backend-tests`, `frontend-tests`, `security`, `docker-build`, `quality-gate`), дождаться зелёного статуса, затем отметить их как required в GitHub UI.
- [High] Подключить Renovate — проверить `.github/renovate.json`, выдать доступ боту и включить на репозитории.
- [High] Список модулей для тестов (10–15) — распределить между исполнителями; приоритет: безопасность, авторизация, налоги, миграции, импорт.
- [Medium] Включить `quality-gate-strict` через 2 недели при достижении порогов (backend ≥ 35%, frontend ≥ 25%, combined ≥ 30%).
- [Medium] Настроить nightly `full-tests` (backend/frontend) — расписание уже добавлено (`0 2 * * *`).
- [Medium] Документировать docker build cache и публикацию артефактов (Trivy SARIF, junit/coverage/lcov) — дополнить `docs/quality.md` и README.
