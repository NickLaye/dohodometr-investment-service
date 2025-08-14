# REPORT_C — Приведение окружений и инструментов к детерминизму

## 1) Версии языков/инструментов

- Добавлены версии окружений:
  - `.nvmrc` → `20`
  - `.python-version` → `3.12.3`
- Frontend остаётся на npm (package-lock.json присутствует); `.npmrc` добавлен с `engine-strict`, `save-exact`.

## 2) Линтеры/форматтеры/типы

- Backend уже имел `ruff`, `black`, `isort`, `mypy` в `pyproject.toml`.
- Frontend — TS strict уже включён в `tsconfig.json`; ESLint/Prettier присутствуют в `package.json`.
- Добавлен `pre-commit` конфиг (`.pre-commit-config.yaml`): ruff, ruff-format, black, isort, yamllint, hadolint (на Dockerfiles), detect-secrets.
- Добавлен `commitlint` конфиг (`.commitlintrc.json`) с Conventional Commits.
- Добавлен строгий `.yamllint.yml`.

## 3) Строгие конфиги реестров

- `.npmrc` без токенов; приватные реестры — только через `NPM_TOKEN` в секретах GitHub/Environments (при необходимости).
- Для Python приватных пакетов — использовать `PIP_INDEX_URL`/`PIP_EXTRA_INDEX_URL` в секретах (не добавлялось в репо).

## 4) Скрипты

- Makefile уже содержит цели для lint/test/scan. Pre-commit и commitlint интегрируются с локальным процессом.

## Риски и next steps

- Убедиться, что в CI установлен commitlint (можно добавить job `lint-commits` на PR), и что pre-commit запускается локально у контрибьюторов.
- При необходимости зафиксировать `corepack`/pnpm — не требуется, так как выбран npm.
