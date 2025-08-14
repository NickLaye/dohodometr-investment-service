<<<<<<< HEAD
# Заголовок PR

Короткое описание изменений и контекст задачи (ссылка на тикет/issue).

## Чек‑лист

- [ ] Тесты: добавлены/обновлены (backend: pytest, frontend: vitest/jest)
- [ ] Миграции БД: alembic upgrade/downgrade включены, проверены локально
- [ ] Фича‑флаги: новая логика за флагом (по умолчанию off), план удаления флага есть
- [ ] Документация: README/CHANGELOG/OpenAPI и dev‑доки обновлены
- [ ] Совместимость: описаны ломающие изменения или подтверждено, что их нет
- [ ] Безопасность: права/валидация/секреты проверены, риск‑анализ выполнен
- [ ] Производительность: оценка влияния, отсутствуют регрессии (бенч/профили)
- [ ] Окружение: новые env переменные добавлены в `env.example` и деплой‑шаблоны
- [ ] Наблюдаемость: метрики/логи/алерты/дэшборды обновлены при необходимости
- [ ] UI: приложены скриншоты/видео, обновлены стили под дизайн‑систему
- [ ] Роллбек‑план: описан простой и безопасный откат

### CI/Branch Protection
- [ ] Smoke проверки зелёные: `backend-tests`, `frontend-tests`
- [ ] Security scan без critical: `security`
- [ ] Docker build проходит: `docker-build`
- [ ] Quality gate (soft): `quality-gate` прошёл, покрытие не ухудшено значительно

## План развертывания / отката

1. Шаги деплоя (миграции, перезапуски, фича‑флаг rollout)
2. Откат (downgrade миграций, выключение флагов, восстановление данных)

## Затронутые области

- backend / frontend / infra / документация

## Дополнительно

- Связанные тикеты/PR: 
- Скриншоты/артефакты: 

=======
>>>>>>> 2795a30 (chore(repo): add PR template, commitlint config and repo hygiene updates for Phase B)
## Краткое описание

Опишите что именно изменено и зачем.

## Тип изменений

- [ ] feat: новая функциональность
- [ ] fix: исправление бага
- [ ] docs: документация
- [ ] chore/ci: инфраструктура/CI/CD
- [ ] refactor/perf/test

## Чек-лист перед PR

- [ ] Соответствует `.cursor/rules` и `DESIGN_SYSTEM.md`
- [ ] Conventional Commits (`type(scope): subject`)
- [ ] Линтеры/типы/тесты зелёные локально
- [ ] Нет секретов и приватных данных

## Связанные задачи/issue

Ссылки на задачи/issue/обсуждения.

## Скрины/лог-выдержки (если уместно)

Вставьте.

## 📋 Description
Brief description of the changes in this PR.

## 🔗 Related Issues
Fixes #(issue_number)
Closes #(issue_number)
Relates to #(issue_number)

## 🚀 Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Maintenance/refactoring
- [ ] ⚡ Performance improvement
- [ ] 🔒 Security fix
- [ ] 🎨 UI/UX improvement

## 🧪 Testing
- [ ] Tests pass locally
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have tested this change in a staging environment

**Test Coverage:**
- Backend: XX%
- Frontend: XX%

## ✅ Required Checks (for main)
- [ ] Backend Tests (CI)
- [ ] Frontend Tests (CI)
- [ ] Security Scan (CI)
- [ ] Docker Build Test (CI)
- [ ] Quality Gate (CI)

## 🔀 Git Workflow
- Base branch: `main` (protected, linear history, squash merge)
- Branch name: `feat|fix|docs|chore|perf|refactor|ci/<scope>-<short>`
- Title follows Conventional Commits: `type(scope): subject`
- Rebased on latest `main`

## 📋 Checklist
### Code Quality
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings or errors

### Security
- [ ] I have considered security implications of my changes
- [ ] No sensitive data is exposed in logs or error messages
- [ ] Authentication and authorization are properly implemented
- [ ] Input validation is in place where needed

### Backend Specific
- [ ] Database migrations are included (if applicable)
- [ ] API documentation is updated (if applicable)
- [ ] Error handling is implemented
- [ ] Logging is appropriate

### Frontend Specific
- [ ] Components are accessible (a11y)
- [ ] Loading states are handled
- [ ] Error states are handled
- [ ] Mobile responsive design is maintained

## 🏷 Auto-labels (optional)
Add labels matching your scope (e.g. `area/backend`, `area/frontend`, `area/infra`, `area/security`).

## 📸 Screenshots (if applicable)
Add screenshots to help explain your changes.

## 🔄 Breaking Changes
List any breaking changes and migration steps required.

## 📝 Additional Notes
Any additional information that reviewers should know.

## 🎯 Reviewer Guidelines
- [ ] Code follows established patterns and conventions
- [ ] Tests cover the new functionality adequately
- [ ] Documentation is clear and up-to-date
- [ ] Performance implications have been considered
- [ ] Security considerations have been addressed

---

**By submitting this PR, I confirm that:**
- [ ] I have read and understood the contributing guidelines
- [ ] I have tested my changes thoroughly
- [ ] I am willing to make any necessary revisions based on feedback
