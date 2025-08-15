# REPORT_A — Анализ состояния (Phase A)

## 1) Обнаруженные артефакты и конфигурация

- **CI/CD**: каталог `.github/workflows` в репозитории отсутствует → нет настроенных GitHub Actions. Это блокер для PR.
- **Git политика**: есть `.editorconfig`, `.gitattributes`, `.gitignore`; есть `.pre-commit-config.yaml` (ruff/black/mypy/eslint/hadolint/yamllint/detect-secrets).
- **Secret scan**: есть `.gitleaks.toml` с allowlist для dev-секретов (compose dev), игнор для build/caches.
- **Языки и версии**:
  - Python: `.python-version` → 3.12.3; `backend/pyproject.toml` → requires-python >=3.12; ruff/mypy/pytest/coverage конфиг присутствуют.
  - Node: `.nvmrc` → 20; `frontend/package.json` engines node >=18 (совместимо, рекомендуем зафиксировать 20 в engines).
- **Backend зависимости**: `backend/requirements.txt` (pinned), `backend/requirements-dev.txt` (pinned). Multi-stage Dockerfile, non-root, healthcheck ok.
- **Frontend**: Next.js 14, TS strict, ESLint/Prettier. Multi-stage Dockerfile, non-root, healthcheck ok.
- **Compose (dev)**: `docker-compose.dev.yml` содержит Postgres/Redis/MinIO/backend/celery/frontend; dev-секреты заданы в env (допустимо для dev, попадают в gitleaks allowlist).
- **Makefile**: цели lint/test/security-scan/ci-test. Замечание: `ci-test` ссылается на `docker-compose.test.yml`, которого нет в репозитории → разрыв.

## 2) Симптомы/риски для push/PR

- Нет GitHub Actions → PR будут без required checks; при включённой защите ветки merge заблокирован.
- `ci-test` ломается из-за отсутствия `docker-compose.test.yml`.
- Dev-секреты в compose могут давать ложные срабатывания gitleaks вне allowlist контекста.

## 3) Branch protection и required checks (фактическое/план)

- Фактическое: локально определить нельзя. Предлагаемый стандарт (синхрон с `.cursor/rules`):
  - backend-tests, frontend-tests, security, docker-build, quality-gate (плюс CodeQL).
- Имена job будут синхронизированы при добавлении workflows в Phase E.

## 4) Вывод

- Основной блокер: отсутствие `.github/workflows/*` и `docker-compose.test.yml`.
- Бэкенд/фронтенд Dockerfile соответствуют требованиям: multi-stage, non-root, healthcheck.
- Контроль качества и типов присутствует (ruff/mypy/eslint/tsc), нужен CI wiring.

## 5) Рекомендации к исправлению (перейдут в Phase E/B)

- Добавить стандартизированные workflows: lint → typecheck → tests → security scan → docker build (и позже deploy). Pin actions по SHA и минимальные permissions.
- Добавить `docker-compose.test.yml` под `make ci-test` или править цель на существующие конфиги.
- Уточнить engines в `frontend/package.json` до Node 20.
- Синхронизировать required checks в GitHub Branch protection с названиями job.

— Дальнейшие изменения будут оформлены отдельным PR (Phase B/C/E) с соответствующими отчётами.


