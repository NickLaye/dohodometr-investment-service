# ⚡ Быстрые правила "Доходометр"

> **Краткий справочник перед каждым изменением**

## 🚨 КРИТИЧЕСКИ ВАЖНО

### ❌ НИКОГДА НЕ ДЕЛАЙ:
- Async функции в Backend
- Новые цвета (только #1F3B35, #C79A63, #63B8A7)
- AsyncSession вместо Session
- Компоненты без типов TypeScript
- Хардкод секретов/паролей

### ✅ ВСЕГДА ДЕЛАЙ:
- Читай `.cursor/rules` перед работой
- Используй `database_sync` для БД
- Типизируй весь код
- Проверяй адаптивность
- Тестируй в темной теме

---

## 🎨 ДИЗАЙН (5 СЕКУНД)

### Цвета:
```css
--primary: #1F3B35     /* Изумрудный */
--accent-1: #C79A63    /* Песочный */  
--accent-2: #63B8A7    /* Мятный */
```

### Шрифты:
- **Manrope** - основной текст
- **Roboto Serif Narrow** - заголовки, цифры

### Кнопки:
- **Основные действия:** мятный цвет
- **Вторичные:** песочный цвет

---

## 💻 КОД (5 СЕКУНД)

### Python Backend:
```python
# ✅ ПРАВИЛЬНО
from app.core.database_sync import get_db
from sqlalchemy.orm import Session

def endpoint(db: Session = Depends(get_db)):
    return result

# ❌ НЕПРАВИЛЬНО  
from app.core.database import get_db
async def endpoint(db: AsyncSession = ...):
```

### TypeScript Frontend:
```typescript
// ✅ ПРАВИЛЬНО
interface Props {
  data: Portfolio;
}
export function Component({ data }: Props) {

// ❌ НЕПРАВИЛЬНО
export function Component({ data }) {
```

---

## 📋 ПЕРЕД КОММИТОМ (10 СЕКУНД)

```bash
□ Дизайн соответствует системе
□ Код типизирован  
□ БД синхронная (database_sync)
□ Адаптивность проверена
□ Синтаксис валиден
□ Секреты не хардкодятся
```

---

## 🔧 БЫСТРЫЕ КОМАНДЫ

```bash
# Проверка синтаксиса
python3 -m py_compile backend/app/main.py

# Проверка типов
npm run type-check

# Проверка линтера
npm run lint
```

---

**Полные правила:** `.cursor/rules` | **Дизайн:** `DESIGN_SYSTEM.md`
