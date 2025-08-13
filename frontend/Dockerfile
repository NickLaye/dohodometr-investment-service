# Multi-stage build для оптимизации размера
FROM node:20-alpine AS builder

# Метаданные
LABEL maintainer="Dohodometr Team"
LABEL version="1.0.0"
LABEL description="Dohodometr Frontend"

# Рабочая директория
WORKDIR /app

# Копирование package файлов
COPY package*.json ./

# Установка зависимостей
RUN npm install && npm cache clean --force

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Production стадия
FROM node:20-alpine AS runner

# Создание пользователя приложения
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Рабочая директория
WORKDIR /app

# Копирование необходимых файлов из builder
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Переключение на пользователя приложения
USER nextjs

# Порт приложения
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Команда запуска
CMD ["node", "server.js"]
