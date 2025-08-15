# REPORT_B — Git и история репозитория

## 1) Секреты и большие файлы
- В дереве присутствуют DEV-плейсхолдеры в `docker-compose.dev.yml` (допустимо; внесены в `.gitleaks.toml` allowlist). Прод-секретов в репозитории не обнаружено.
- Рекомендуется прогнать `gitleaks` по рабочей копии и истории; при нахождении реальных секретов — ротация и план переписывания истории по согласованию.
- Проверка крупных бинарников в истории не выполнялась автоматически; рекомендуется анализ и, при необходимости, перевод в Git LFS.

## 2) Политики Git
- `.gitignore`, `.gitattributes`, `.editorconfig` — присутствуют; предлагаемое улучшение `.gitignore`: игнор `coverage.xml`, `htmlcov/`, `reports/`.
- Добавлены в Phase B: `commitlint.config.js` и PR-шаблон `.github/PULL_REQUEST_TEMPLATE.md`.

## 3) Commit-стиль и хуки
- В корне есть `package.json` с Husky/Commitlint; `.husky/commit-msg` вызывает commitlint. Conventional Commits включены.

## 4) Branch protection / Required checks
- Требуется включить защиту ветки `main` и согласовать required checks после добавления CI в Phase E.

## 5) Команды для проверок (безопасные)

```bash
# Secret scan (локально, без истории)
docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:latest detect -s /repo -c /repo/.gitleaks.toml --redact || true

# Secret scan по истории
docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:latest detect -s /repo -c /repo/.gitleaks.toml --redact --no-git=false || true

# Крупные файлы в рабочей копии (top 20)
git ls-files -z | xargs -0 -I{} du -b {} 2>/dev/null | sort -nr | head -n 20
```

## 6) Изменения в этом PR (Phase B)
- Добавлены: `commitlint.config.js`, `.github/PULL_REQUEST_TEMPLATE.md`.
- Улучшен `.gitignore` и `.gitattributes` (диф для coverage.xml, игнор отчётов покрытия).
