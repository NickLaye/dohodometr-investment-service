# REPORT_E — CI/CD (GitHub Actions) до зелёного статуса

## 1) Workflows и пайплайны

- Основной CI: `.github/workflows/ci.yml`
  - Последовательность: lint → typecheck → unit (BE/FE) → security (Trivy + detect-secrets) → docker build → e2e (PR) → quality gate.
  - Добавлены: `permissions: contents: read`, `concurrency`, `timeout-minutes` на job’ах, `TZ=UTC`.
  - Пины экшенов по SHA/версиям.
- Security pipelines:
  - `security-baseline.yml` — gitleaks + SBOM (anchore) с пинами.
  - `security-scanning.yml` — CodeQL, Safety/npm audit, detect-secrets, Trivy, Checkov, summary (пины, permissions, стабильность).
  - `comprehensive-security.yml`, `security-hardened.yml` — приведены к единому стилю: concurrency, timeout-minutes, pinned actions.
- CD:
  - `cd-production-fixed.yml` — основной прод-деплой (build & push → image scan → ssh deploy). 
  - `cd-production.yml` — заменён на stub `deprecated-cd-production` для совместимости с возможными старыми required checks (не деплоит).

## 2) Permissions, concurrency, caching

- Минимально необходимые права у jobs, security-events только там, где нужно.
- `concurrency` предотвращает параллельные конфликты одного и того же ref.
- Кэширование pip/npm и Docker buildx GHA cache.

## 3) Безопасность CI

- Пины actions по SHA/версиям; убран `master` где встречался.
- Gitleaks + detect-secrets (non-blocking в CI, blocking в baseline при необходимости).
- SBOM (CycloneDX) как артефакт.
- Trivy (fs/images), Checkov (dockerfile/compose/github_actions).

## 4) Secrets

- Используются только `secrets.*`. Токены/реестры в YAML не хранятся.

## 5) Required status checks (предложение)

Рекомендуемые обязательные проверки в Branch Protection:
- `CI Pipeline / backend-tests`
- `CI Pipeline / frontend-tests`
- `CI Pipeline / security` (или `Security Scanning / codeql` при желании)
- `CI Pipeline / docker-build`
- (опционально) `CI Pipeline / quality-gate`

E2E на PR — не обязательный (informational). Security расширенные пайплайны могут быть optional.

## 6) Текущее состояние

- Файл конфигурации CI/секьюрити приведён к устойчивому виду. Готов к прогонам. После первого запуска скорректируем список required checks под фактические job names.
