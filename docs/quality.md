# Качество: покрытие, цели и правила

## Текущее покрытие (ориентиры)
- Backend: ~35–45% (по `coverage.xml` в CI)
- Frontend: ~25–35% (по `lcov.info` в CI)
- Combined: ~30–40%

CI собирает и сохраняет артефакты покрытия:
- `backend/coverage.xml` (pytest — cobertura XML)
- `frontend/coverage/lcov.info` (vitest/jest — LCOV)

## Цели на 2 спринта
- Backend: 50% → 65%
- Frontend: 35% → 50%

Механика контроля:
- `quality-gate` — мягкий, печатает сводку и не падает.
- `quality-gate-strict` — опциональный, с порогами: backend ≥ 35%, frontend ≥ 25%, combined ≥ 30% (включаем через 2 недели и повышаем вместе с прогрессом).

## Правило приоритета
- Критичные модули тестируются в первую очередь. Определение критичности: безопасность, расчёты налогов/денег, авторизация, миграции, импорт/экспорт данных, интеграции.

## Как локально собрать метрики
- Backend: `make backend-test-all` или быстрее `make backend-test-fast`
- Frontend: `make fe-test` (покрытие по конфигу фронта)
- Сводка: `make quality-gate` (артефакты в `reports/`)

## Отчёт в PR
- Запуск CI даёт артефакты покрытия; сводка отображается в job `quality-gate`.
- Для «полных» прогона тестов поставьте label `full-tests` на PR или запустите workflow вручную (`workflow_dispatch`).


