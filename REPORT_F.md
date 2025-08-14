# REPORT_F — Сборка контейнеров и артефактов

## 1) Dockerfile улучшения

- Backend `backend/Dockerfile`:
  - Включён BuildKit syntax, кэш pip (`--mount=type=cache,target=/root/.cache/pip`).
  - Non-root user, HEALTHCHECK, PYTHONDONTWRITEBYTECODE, очистка apt-кэшей.
- Frontend `frontend/Dockerfile`:
  - Включён BuildKit syntax, кэш npm (`--mount=type=cache,target=/root/.npm`).
  - Non-root user, HEALTHCHECK, отключена телеметрия, обновления пакетов.

## 2) Скан и размер

- В CI включены Trivy сканы файловой системы и образов.
- Следующий шаг: добавить multi-arch slim-образы с pinned digest (по готовности релизов) и проверку `apk add --no-cache` на минимальность.

## 3) docker-compose (интеграционные тесты)

- E2E job поднимает сервисы, ждёт health и затем выполняет Playwright.

## 4) Next steps

- Вынести ARG/labels версий в build pipeline (метаданные) и добавлять SBOM как артефакт релиза.
- При желании перейти на distroless/ubi-micro после совместимости.
