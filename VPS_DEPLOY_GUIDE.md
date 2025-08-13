# 🚀 Пошаговое руководство по деплою YouInvest на VPS

## 🎯 **Что получится:**
- **Полнофункциональный YouInvest** на вашем домене
- **HTTPS с автоматическими SSL сертификатами**
- **Автоматические бэкапы** каждый день
- **Мониторинг и метрики** в реальном времени
- **Автозапуск** при перезагрузке сервера

---

## 📋 **Шаг 1: Подготовка VPS**

### 🖥️ **Закажите VPS с характеристиками:**
- **OS:** Ubuntu 22.04 LTS  
- **RAM:** 4 GB (минимум)
- **CPU:** 2 ядра
- **SSD:** 40 GB
- **IP:** Статический

### 🔑 **Подключитесь по SSH:**
```bash
ssh root@YOUR_SERVER_IP
```

---

## 📋 **Шаг 2: Запуск автоустановки**

### 📥 **Скачайте скрипт установки:**
```bash
wget https://raw.githubusercontent.com/YOUR_REPO/main/deploy_vps.sh
chmod +x deploy_vps.sh
```

### 🚀 **Запустите установку:**
```bash
sudo bash deploy_vps.sh
```

### ⏳ **Что происходит (15-20 минут):**
1. **Проверка системы** и ресурсов
2. **Обновление ОС** и установка зависимостей  
3. **Установка Docker** и Docker Compose
4. **Настройка безопасности** (firewall, fail2ban)
5. **Создание пользователя** приложения
6. **Генерация паролей** и ключей шифрования
7. **Создание конфигураций** для production
8. **Настройка автозапуска** и бэкапов

---

## 📋 **Шаг 3: Настройка домена**

### 🌐 **Настройте DNS в DuckDNS:**

1. **Зайдите на:** https://www.duckdns.org
2. **Создайте домен:** `yourinvest` (или любой другой)
3. **Установите IP:** Ваш IP сервера
4. **Сохраните**

### 🔗 **Или в любом DNS провайдере:**
```
Тип: A
Имя: yourinvest.duckdns.org  
Значение: YOUR_SERVER_IP
TTL: 300
```

---

## 📋 **Шаг 4: Запуск сервиса**

### 🚀 **Запустите YouInvest:**
```bash
sudo systemctl start youinvest
```

### 🔍 **Проверьте статус:**
```bash
sudo systemctl status youinvest
```

### 📊 **Посмотрите логи:**
```bash
cd /opt/youinvest
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🎉 **Шаг 5: Готово!**

### 🌐 **Ваш сервис доступен по адресам:**

- **🎯 Главное приложение:** https://yourinvest.duckdns.org
- **📚 API документация:** https://yourinvest.duckdns.org/api/docs  
- **❤️ Health check:** https://yourinvest.duckdns.org/health
- **📊 Traefik панель:** https://traefik.yourinvest.duckdns.org

### 🔐 **Первая настройка:**
1. **Откройте** https://yourinvest.duckdns.org
2. **Зарегистрируйтесь** как первый пользователь
3. **Настройте** свой профиль
4. **Создайте** первый портфель

---

## 🛠️ **Управление сервисом**

### 🔄 **Основные команды:**
```bash
# Запуск
sudo systemctl start youinvest

# Остановка  
sudo systemctl stop youinvest

# Перезапуск
sudo systemctl restart youinvest

# Статус
sudo systemctl status youinvest

# Автозапуск (уже включен)
sudo systemctl enable youinvest
```

### 📊 **Мониторинг:**
```bash
# Логи всех сервисов
cd /opt/youinvest
docker-compose -f docker-compose.prod.yml logs -f

# Логи конкретного сервиса
docker logs youinvest-backend -f
docker logs youinvest-frontend -f

# Статус контейнеров
docker ps

# Использование ресурсов
docker stats
```

### 💾 **Бэкапы:**
```bash
# Ручной бэкап
/opt/youinvest/backup.sh

# Просмотр бэкапов
ls -la /opt/youinvest/backups/

# Восстановление из бэкапа
docker exec -i youinvest-postgres psql -U youinvest_user youinvest_prod < backup_file.sql
```

---

## 🔧 **Настройка конфигурации**

### ⚙️ **Основные настройки в `/opt/youinvest/.env`:**
```bash
# Редактирование конфигурации
sudo nano /opt/youinvest/.env

# Применение изменений
sudo systemctl restart youinvest
```

### 🔑 **Смена паролей:**
```bash
# Сгенерировать новый пароль
openssl rand -base64 32

# Обновить в .env файле
sudo nano /opt/youinvest/.env

# Перезапустить
sudo systemctl restart youinvest
```

---

## 🚨 **Решение проблем**

### ❌ **Сервис не запускается:**
```bash
# Проверить логи systemd
sudo journalctl -u youinvest -f

# Проверить статус Docker
sudo systemctl status docker

# Перезапустить Docker
sudo systemctl restart docker

# Проверить права доступа
sudo chown -R youinvest:youinvest /opt/youinvest
```

### 🌐 **Сайт не открывается:**
```bash
# Проверить DNS
nslookup yourinvest.duckdns.org

# Проверить порты
sudo ufw status
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Проверить Traefik
docker logs youinvest-traefik -f
```

### 🗄️ **Проблемы с БД:**
```bash
# Подключение к PostgreSQL
docker exec -it youinvest-postgres psql -U youinvest_user youinvest_prod

# Проверка места на диске
df -h

# Очистка логов Docker
docker system prune -f
```

---

## 📈 **Мониторинг и метрики**

### 📊 **Grafana дашборды:**
- **URL:** https://yourinvest.duckdns.org:3000
- **Логин:** admin  
- **Пароль:** (указан в .env файле)

### 🔍 **Prometheus метрики:**
- **URL:** https://yourinvest.duckdns.org:9090

### 📱 **Мониторинг через Telegram/Email:**
```bash
# Настройка уведомлений (опционально)
sudo nano /opt/youinvest/monitoring/alerts.yml
```

---

## 🔒 **Безопасность**

### 🛡️ **Что уже настроено:**
- ✅ **UFW Firewall** (только SSH, HTTP, HTTPS)
- ✅ **fail2ban** (защита от брутфорса)
- ✅ **Let's Encrypt SSL** (автообновление)
- ✅ **Docker security** (unprivileged containers)
- ✅ **Сильные пароли** (автогенерация)

### 🔐 **Дополнительная защита:**
```bash
# Отключение root SSH (рекомендуется)
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
sudo systemctl restart sshd

# Настройка SSH ключей
ssh-keygen -t rsa -b 4096
ssh-copy-id youinvest@YOUR_SERVER_IP

# Обновления безопасности (автоматически)
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

---

## 💰 **Расходы и масштабирование**

### 💸 **Ежемесячные расходы:**
- **VPS:** $24-30/месяц
- **Домен:** $0 (DuckDNS)
- **SSL:** $0 (Let's Encrypt)
- **Всего:** ~$25-30/месяц

### 📈 **Масштабирование при росте:**
- **100+ пользователей:** Увеличить RAM до 8GB
- **500+ пользователей:** Добавить 2-4 CPU ядра
- **1000+ пользователей:** Вынести БД на отдельный сервер

---

## 🆘 **Поддержка**

### 📞 **Получить помощь:**
1. **Проверьте логи** (см. команды выше)
2. **Создайте issue** в GitHub репозитории
3. **Приложите логи** и описание проблемы

### 📚 **Полезные ссылки:**
- [Docker документация](https://docs.docker.com/)
- [Traefik документация](https://doc.traefik.io/traefik/)
- [PostgreSQL документация](https://www.postgresql.org/docs/)

---

## 🎉 **Поздравляем!**

**У вас теперь есть полностью функциональный YouInvest сервис!**

- **🔒 Безопасный** (HTTPS, firewall, пароли)
- **📊 Мониторимый** (логи, метрики, health checks)  
- **💾 Резервируемый** (автоматические бэкапы)
- **🚀 Масштабируемый** (Docker, простое обновление)

**Наслаждайтесь инвестированием! 📈💰**
