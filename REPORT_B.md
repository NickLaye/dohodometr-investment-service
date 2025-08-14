# REPORT_B — Блокеры уровня Git/репозитория (до CI)

## 1) Секреты / Push Protection

- Добавлен `.gitleaks.toml` с allowlist для DEV-плейсхолдеров (`docker-compose.dev.yml`) и игнором бинарей/сборок.
- Рекомендация: сгенерировать `.secrets.baseline` и закрепить в репо, обновлять при изменениях dev-конфига.
- В `docker-compose.dev.yml` обнаружены dev-значения (`MINIO_ROOT_PASSWORD=password123`, `SECRET_KEY=dev-...`, `JWT_SECRET_KEY=dev-...`). Это допускается для локалки, но может давать алерты. Перенос в `.env` необязателен, baseline/allowlist настроен.
- Прод-секреты не хранятся в репо; используются `secrets.*`/env на CI/CD и в `deployment`.

### План ротации (если реальные секреты будут найдены gitleaks)

1. Немедленная ревокация и выпуск новых ключей/паролей (DB/Redis/MinIO/API).
2. Перенос значений в secrets/env. Обновление `.env.example` только с плейсхолдерами.
3. Если секрет в истории Git: `git filter-repo` по непубличной/незащищённой ветке, остановка защиты веток, коммуникация команде, форс-пуш, пересоздание PR при необходимости. Риски: инвалидация хэшей/PR.

## 2) Большие файлы (>100MB) / LFS

- Проверка истории не запускалась автоматически. Рекомендация: анализ largest objects и при необходимости `git lfs migrate import` + обновление `.gitattributes`.
- Добавлены правила бинарей в `.gitattributes`.

## 3) CRLF/пермишены/симлинки

- Добавлены:
  - `.editorconfig` (LF, финальная новая строка, отступы; табы только для `Makefile`).
  - `.gitattributes` (`* text=auto eol=lf`, бинарные расширения, -diff для `package-lock.json`).
- Исполняемые биты — контролировать ревью/CI (hadolint/checkov покрывают часть кейсов).

## 4) Branch protection / PR rules

- `CODEOWNERS` настроен; требуется заменить плейсхолдеры реальными командами (`@yourusername` и т.п.).
- `PULL_REQUEST_TEMPLATE.md` уже есть.

## 5) CI workflow блокеры

- Критично: `.github/workflows/security.yml` содержал 2 workflow в одном файле → разделил на:
  - `.github/workflows/security-baseline.yml`
  - `.github/workflows/security-scanning.yml`
  и удалил исходный конфликтный `security.yml`.
- Дубликаты CD: удалён `cd-production.yml`, оставлен `cd-production-fixed.yml` как единственный pipeline прод-деплоя.
- Все новые экшены закреплены по SHA (supply-chain hardening).

## Изменения в репо (PR: repo-hygiene)

- Добавлены: `.editorconfig`, `.gitattributes`, `.gitleaks.toml`.
- Разделён security workflow, удалены конфликтные/дублирующие YAML.
- Секреты не добавлялись.

## Команды для локальной проверки (ручной запуск)

```bash
# Secret scan (локально)
GITLEAKS_DETECT_CONFIG=.gitleaks.toml gitleaks detect --redact --verbose || true

# Крупные файлы (top 20)
git ls-files -z | xargs -0 -I{} du -b {} 2>/dev/null | sort -nr | head -n 20
```
