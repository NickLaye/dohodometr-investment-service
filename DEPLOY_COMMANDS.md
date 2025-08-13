# 🚀 **КОМАНДЫ ДЛЯ ДЕПЛОЯ - ВЫПОЛНЯТЬ ПО ПОРЯДКУ**

## **ШАГ 1: СОХРАНЕНИЕ ИЗМЕНЕНИЙ С СЕРВЕРА** 🚨

```bash
# Подключаемся к серверу
ssh root@185.23.35.41

# Скачиваем скрипт для сохранения изменений
curl -O https://raw.githubusercontent.com/NickLaye/dohodometr-investment-service/main/deployment/save_server_changes.sh

# Делаем исполняемым
chmod +x save_server_changes.sh

# ЗАПУСКАЕМ СОХРАНЕНИЕ
./save_server_changes.sh
```

**Результат:** Создастся бэкап `/opt/server_changes_YYYYMMDD_HHMMSS.tar.gz`

---

## **ШАГ 2: СКАЧИВАЕМ ИЗМЕНЕНИЯ НА ЛОКАЛЬНУЮ МАШИНУ**

```bash
# С локальной машины (новый терминал)
scp root@185.23.35.41:/opt/server_changes_*.tar.gz ./
scp root@185.23.35.41:/opt/server_changes_*_report.txt ./

# Смотрим что там
cat server_changes_*_report.txt
```

---

## **ШАГ 3: ПРОВЕРЯЕМ ИЗМЕНЕНИЯ**

```bash
# Распаковываем бэкап
tar -xzf server_changes_*.tar.gz

# Проверяем отличия в ключевых файлах
diff -r backend/ server_backup/backend/ | head -20
```

---

## **ШАГ 4: GIT DEPLOY** 🚀

```bash
# Возвращаемся на сервер
ssh root@185.23.35.41

# Скачиваем Git Deploy скрипт
curl -O https://raw.githubusercontent.com/NickLaye/dohodometr-investment-service/main/deployment/git_deploy.sh

# Делаем исполняемым  
chmod +x git_deploy.sh

# ЗАПУСКАЕМ ДЕПЛОЙ
./git_deploy.sh
```

**Время:** ~10-15 минут

---

## **ШАГ 5: ПРОВЕРКА РЕЗУЛЬТАТА**

```bash
# Проверяем что все работает
curl -I https://dohodometr.ru/
curl -s https://dohodometr.ru/api/v1/ | jq
curl -s https://dohodometr.ru/health | jq

# Проверяем контейнеры
docker-compose ps
```

---

## **ОЖИДАЕМЫЙ РЕЗУЛЬТАТ:**

- ✅ `https://dohodometr.ru` - React приложение (НЕ статическая страница)
- ✅ `https://dohodometr.ru/api/v1/` - API работает
- ✅ `https://dohodometr.ru/health` - Health check работает
- ✅ Все контейнеры запущены и здоровы

---

**НАЧИНАЕМ С ПЕРВОГО ШАГА!** ⬇️
