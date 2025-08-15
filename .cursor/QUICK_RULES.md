# ⚡ Быстрые правила «Доходометр» (v3)

> Прочти перед коммитом. Полная версия: `.cursor/rules`, дизайн: `DESIGN_SYSTEM.md`.

## 🚨 Никогда не делай
- Async в Backend, `AsyncSession`
- Новые цвета/шрифты
- Хардкод секретов/паролей
- Компоненты без типов/адаптива
- Изменения без тестов/линтов

## ✅ Всегда делай
- Задачи только через **Оркестратора** (он сам подключит роли)
- Сверяйся со **стратегией** и **дизайн‑системой**
- Полная типизация (TS/Python), синхронная БД
- a11y + тёмная тема + производительность
- Локальные проверки:
```bash
python3 -m py_compile backend/app/**/*.py
npm run type-check && npm run lint
```

## 🔀 Git (кратко)

- **База:** `main` (linear history, Squash & Merge only)
- **Ветки:** `feat|fix|docs|chore|perf|refactor|ci/<scope>-<short>`
- **Коммиты/PR:** Conventional Commits `type(scope): subject`
- **Merge-коммиты:** нельзя → делай `git rebase origin/main`
- **Перед PR:** ребейз на `main`, локальные проверки зелёные
- **CI (для main):** backend-tests, frontend-tests, security, docker-build, quality-gate

Примеры:
```bash
git checkout -b feat/rules-v3
git commit -m "docs(rules): update v3 git workflow"  # формат
git fetch origin && git rebase origin/main            # линейная история
```

🎨 Цвета (памятка)

`#1F3B35` • `#C79A63` • `#63B8A7` • `#F8F9F8` • `#2C2E2D`

Шрифты: Manrope, Roboto Serif Narrow

📋 Чек‑лист (10 сек)

□ Соответствует DESIGN_SYSTEM.md
□ Типизация ОК (TS/Python)
□ БД sync + миграции оформлены
□ Адаптив/доступность ОК
□ Секреты не хардкодятся
□ Документация обновлена
□ Для юр. аспектов — check по РФ

⸻

ПОСЛЕ ИЗМЕНЕНИЙ
	•	Сделай PR в main и убедиcь, что CI зелёный.
