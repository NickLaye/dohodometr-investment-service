# Сценарии вызова агентов

## A. Оркестратор по умолчанию (рекомендовано)

<<include: agents/ai-project-lead.md>>

[TASK]
Сделать импорт выписок (CSV/XLSX) + расчёт доходности + график в админке.

## B. Тонкая пачка (Lead + целевая роль + карточки остальных)

<<include: agents/ai-project-lead.md>>
<<include: agents/ai-fullstack-developer.md>>
<<include: agents/cards/qa-engineer.md>>
<<include: agents/cards/devops-engineer.md>>

[TASK]
…

## C. Конвейер (последовательно)
1) Lead → SPEC.md
2) Dev/UX → код и макеты
3) QA/Legal → проверка и вердикт

Подключай карточки, если нужен краткий контекст без перегрузки промпта.


