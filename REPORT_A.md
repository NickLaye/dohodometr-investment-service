# REPORT_A — Сбор симптомов и конфигураций

## 1) Входные артефакты (найдено в репозитории)

- **Workflows** (`.github/workflows`):
  - `ci.yml` — CI: backend-tests, frontend-tests, security (Trivy + detect-secrets), docker-build, e2e-tests (PR), quality-gate.
  - `security.yml` — ВНИМАНИЕ: файл содержит два независимых workflow в одном YAML (двойной верхнеуровневый `name:`) → потенциальная ошибка парсинга GitHub Actions.
  - `security-hardened.yml` — Укреплённые security-пайплайны (Gitleaks, CodeQL, SBOM, dependency audit, Docker scan, Checkov, summary).
  - `comprehensive-security.yml` — Расширенная security-конвейеризация (пре-проверки, backend/frontend security, контейнеры, SBOM, pen-test, summary).
  - `cd-production.yml` и `cd-production-fixed.yml` — Два похожих CD на прод, есть риск двойного деплоя/дублирования статусов.

- **CODEOWNERS**: `.github/CODEOWNERS` — назначены владельцы для секьюрити-критичных путей, CI/CD и документации (плейсхолдеры `@yourusername`, `@security-team`, и т.д.).

- **Документация/политики/лицензии**:
  - `README.md` — подробный обзор, dev/prod запуск, мониторинг, тесты.
  - `CONTRIBUTING.md` — гайд, Conventional Commits, тест/линт чек-листы перед PR.
  - `SECURITY.md` — политика безопасной разработки, контакт `security@investment-service.ru`.
  - `LICENSE` — MIT (2025, Investment Service).

- **Lock/менеджеры пакетов**:
  - Frontend: `frontend/package-lock.json` (npm). Yarn/pnpm lock не обнаружены.
  - Backend: `backend/requirements.txt`, `backend/requirements-dev.txt`. Poetry/Pipenv lock не обнаружены.

- **Docker/Compose/Infra**:
  - Backend: `backend/Dockerfile` (multi-stage, non-root, healthcheck); dev-файл `backend/Dockerfile.dev` (есть в дереве, используется в compose; содержимое не просматривалось в этом отчёте).
  - Frontend: `frontend/Dockerfile` (multi-stage, non-root, healthcheck); dev-файл `frontend/Dockerfile.dev`.
  - Compose (dev): `docker-compose.dev.yml` — Postgres, Redis, MinIO, backend, celery, frontend; содержит dev-секреты в env (см. симптомы ниже).
  - Compose (prod): `deployment/docker-compose.production.yml` — Traefik, backend, frontend, Postgres, Redis, Uptime Kuma, healthchecks и security headers.
  - Мониторинг: `infra/prometheus/prometheus.yml`, `infra/prometheus/alerts.yml`; Traefik dynamic: `infra/traefik/dynamic.yml` (CSP, HSTS, CORS, rate-limit).

- **Конфиги качества/типов**:
  - Backend: `backend/pyproject.toml` (ruff, mypy, pytest, coverage ≥80%).
  - Frontend: `frontend/package.json` (скрипты lint/type-check/test/e2e), `tsconfig.json` (наличие подтверждено структурой, содержимое будет учтено в последующих фазах).

## 2) Симптомы и риски (до запуска пайплайнов)

- **[Блокер CI] Некорректный YAML в `.github/workflows/security.yml`**:
  - Файл содержит два верхнеуровневых workflow в одном документе (двойной ключ `name:` и повтор `on/jobs`). GitHub Actions обрабатывает по одному workflow на файл → высокая вероятность ошибки парсинга/игнора части шагов.

- **[Риск CD] Дубликаты прод-деплоя**:
  - Имеются оба файла: `cd-production.yml` и `cd-production-fixed.yml` с одинаковым назначением. Риск: гонки, двойной запуск, путаница в required checks.

- **Secret Scanning / Push Protection**:
  - В `docker-compose.dev.yml` присутствуют явные dev-секреты и дефолтные пароли (`MINIO_ROOT_PASSWORD=password123`, `SECRET_KEY=dev-...`, `JWT_SECRET_KEY=dev-...`, `REDIS без пароля` и т.п.).
  - В прод-композе секреты ожидаются из `secrets.*`/env (ок), но наличие dev-секретов в репозитории может триггерить Gitleaks/Secret Scanning на PR (ложноположительные или настоящие, в зависимости от правил). Требуется baseline/игнор для dev и строгие правила для prod.

- **Pinning экшенов**:
  - Часть экшенов закреплена по SHA (👍), часть — по `v*` или `master` (например, Trivy `@master` в ряде файлов) → риск supply-chain. Требуется унификация pin по SHA.

- **Branch Protection / Required checks (предположение)**:
  - Вероятные обязательные статусы: `CI Pipeline / backend-tests`, `CI Pipeline / frontend-tests`, `CI Pipeline / security`, `CI Pipeline / docker-build`, возможно `quality-gate`; а также CodeQL из security workflows.
  - Из-за некорректного `security.yml` и дубликатов CD — возможны «Required check missing» или «Expected — Waiting»/падения.

- **Крупные файлы/LFS**:
  - На данном этапе не выявлялись, требуется прогон истории (см. Фаза B — gitleaks/LFS сканы).

- **CRLF/пермишены/симлинки**:
  - `.editorconfig` и `.gitattributes` в корне не обнаружены → риск дрейфа EOL/пермишенов между ОС.

## 3) Вывод по Фазе A

- Репозиторий хорошо подготовлен к CI/CD и секьюрити (CodeQL, SBOM, Trivy, Checkov), но есть критичные блокеры формата/workflow-дубликатов.
- Высокий риск ложных алармов по secret scanning из-за dev-значений в compose. Нужна нормализация (baseline/исключения) и строгая политика для prod.
- Нет явных следов Terraform/K8s в дереве (используется Traefik + docker-compose).

## 4) Следующие шаги (под Фазу B/C/D намечено)

- Разнести `security.yml` на отдельные валидные workflow-файлы или оставить один, убрав дубликат разделов.
- Выбрать и оставить один CD (`cd-production.yml`), второй удалить/объединить, согласовать названия job’ов с Branch Protection.
- Добавить `.editorconfig`, `.gitattributes` и `.gitignore` актуальные для проекта.
- Включить/настроить `gitleaks` и прогнать по всей истории, подготовить baseline и ротацию при необходимости.
- Проверить LFS/крупные файлы в истории, при необходимости подготовить план переписывания.

— Конкретные исправления и PR будут отражены в REPORT_B/… (следующие фазы).


