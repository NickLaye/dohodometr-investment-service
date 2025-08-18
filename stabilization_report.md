## Stabilization Report — Investment Service

Дата: 2025-08-15

### Итоговая таблица проблем (текущее состояние)

| Блок | Кол-во ошибок | Критичность | Тип проблемы | Пример ошибки |
|---|---:|---|---|---|
| docker-build | 0 | low | сборка | Build succeeded (local/app:ci) |
| backend smoke-тесты | 0 | high → resolved | тест | Было: settings.ENVIRONMENT == 'testing' vs 'development' (tests/unit/test_config.py:24); пагинация портфелей возвращала 3 вместо 2 |
| frontend lint | 0 | medium → resolved | линт | reports/frontend_lint.txt: OK |
| frontend types | 0 | medium → resolved | типы | reports/frontend_types.txt: OK |
| quality-gate | 0 (низкое покрытие) | medium | качество | Combined coverage: 23.90% (reports/quality_summary.md) |
| security (node) | 0 | - | уязвимость | security_node.txt: Passed npm audit |
| security (python) | 0 high/critical после апдейта | high → mitigated | уязвимость | safety/pip-audit: gunicorn<23, python-multipart<0.0.19, cryptography<44 — обновлено |
| flaky tests | 0 | low | тест | reports/flaky_report.md: флейки не обнаружены |

Примечание: исходные backend фейлы (3) устранены; security high/critical — mitigated обновлением зависимостей.

### Список изменений

- backend/conftest.py
  - Зафиксирован ENVIRONMENT для тестов: ENVIRONMENT=development (устранило расхождение дефолта в Settings)
  - Фикстура auth_headers теперь гарантирует наличие пользователя в БД и генерирует валидный JWT
  - Усилена изоляция тестов: полный reset схемы SQLite между тестами для предотвращения «лишних» записей

- backend/requirements.txt (security hardening)
  - gunicorn 21.2.0 → 23.0.0
  - python-jose 3.3.0 → 3.4.0
  - python-multipart 0.0.6 → 0.0.19
  - cryptography 42.0.0 → 44.0.1
  - aiohttp 3.9.1 → 3.12.14
  - jinja2 3.1.3 → 3.1.6

### Прогон проверок

- make docker-ci — OK
- make backend-test-fast — 122 passed, 0 failed
- make fe-lint — OK
- make fe-types — OK
- make quality-gate — OK (coverage: backend 33.66%, frontend 16.30%, combined 23.90%)

### Рекомендации по предотвращению регрессий

- Мигрировать валидаторы Pydantic на v2 (@field_validator, model_dump) для устранения deprecation warning'ов
- Добавить ruff в окружение CI (quality-gate показал «ruff: command not found»), закрепить конфиг и пороги
- Поднять покрытие тестами до >=50% для backend и >=30% для frontend в ближайшей итерации; постепенно повысить cov-fail-under
- Зафиксировать версии security-значимых библиотек и включить регулярные security сканы (Safety/Bandit) в CI с fail-on-high
- Для e2e/интеграционных тестов — стабильная изоляция БД и фикстур; избегать state leakage


