# Разработка на Windows и WSL

Руководство по установке, запуску и настройке Linux Training Simulator на Windows и в WSL2.

## Содержание

1. [Что можно тестировать на Windows](#что-можно-тестировать-на-windows)
2. [Быстрый старт в WSL](#быстрый-старт-в-wsl)
3. [Доступ из локальной сети](#доступ-из-локальной-сети)
4. [Режим разработки (Mock)](#режим-разработки-mock)
5. [Решение проблем](#решение-проблем)

---

## Что можно тестировать на Windows

### ✅ Полностью работает на Windows:

1. **Frontend (React)** - весь интерфейс, навигация, взаимодействие с API
2. **Backend API (FastAPI)** - все API endpoints, логика проверки заданий, система прогресса
3. **Логика приложения** - управление миссиями, проверка выполнения заданий, система достижений

### ❌ Требует Linux:

1. **Podman/контейнеры** - Podman не работает нативно на Windows
2. **Реальные песочницы** - запуск контейнеров, VNC подключения, терминалы

---

## Быстрый старт в WSL

### Предварительные требования

1. **WSL 2** установлен и настроен
   - Проверьте: `wsl --version` в PowerShell
   - Если не установлен: `wsl --install`

2. **Docker Desktop для Windows** (рекомендуется)
   - Скачайте: https://www.docker.com/products/docker-desktop
   - Установите и запустите Docker Desktop
   - Включите интеграцию с WSL в настройках Docker Desktop

### Установка и запуск

**Установка (один раз)**:
```bash
cd /path/to/AstraDiplom
chmod +x scripts/quickstart-wsl.sh
./scripts/quickstart-wsl.sh
```

**Запуск**:
```bash
./start-demo-wsl.sh
```

Откройте в браузере Windows: **http://localhost:3000**

**Остановка**:
```bash
./stop-demo.sh
```

### Особенности WSL

**PostgreSQL**:
```bash
# Запуск PostgreSQL
sudo service postgresql start

# Проверка статуса
sudo service postgresql status
```

**Docker**:
- Установите Docker Desktop для Windows
- Включите интеграцию с WSL в настройках
- Docker будет доступен в WSL автоматически

Проверка:
```bash
docker --version
docker info
```

**Сеть**:
- Frontend и Backend доступны на `localhost` как в WSL, так и в Windows
- Порт 3000 (Frontend) и 8000 (Backend) пробрасываются автоматически

---

## Доступ из локальной сети

WSL2 использует виртуальную сеть, изолированную от локальной сети Windows. Для доступа с других машин требуется настройка.

### Способ 1: Mirrored Networking Mode (Рекомендуется) ⭐

**Преимущества:**
- Настраивается один раз
- Работает автоматически после перезапуска WSL
- Не требует обновления после изменения IP адреса

**Шаги:**

1. **Настройка (один раз)**:
   ```powershell
   # Запустите PowerShell от имени администратора
   PowerShell -ExecutionPolicy Bypass -File scripts/setup-wsl-mirrored-networking.ps1
   ```

2. **Перезапустите WSL2**:
   ```powershell
   wsl --shutdown
   # Затем откройте WSL снова
   ```

3. **Запустите приложение**:
   ```bash
   ./start-demo-wsl.sh
   ```

4. **Узнайте IP адрес Windows хоста**:
   ```powershell
   ipconfig | findstr IPv4
   ```

5. **Подключитесь с других машин**:
   - Frontend: `http://<IP_АДРЕС_WINDOWS>:3000`
   - Backend: `http://<IP_АДРЕС_WINDOWS>:8000`

### Способ 2: Port Forwarding

**Недостатки:**
- Требуется запускать скрипт после каждого перезапуска WSL (если IP изменился)

**Шаги:**

1. **Настройка**:
   ```powershell
   # Запустите PowerShell от имени администратора
   PowerShell -ExecutionPolicy Bypass -File scripts/setup-wsl-port-forwarding.ps1
   ```

2. **Запустите приложение**:
   ```bash
   ./start-demo-wsl.sh
   ```

3. **Подключитесь с других машин**:
   - Используйте IP адрес Windows хоста (указан в выводе скрипта)

**Примечание**: Оба скрипта автоматически настраивают Windows Firewall.

### Проверка работы

**На машине с WSL:**
```bash
# Проверьте, что порты слушают на всех интерфейсах
netstat -tuln | grep -E ':(3000|8000)'
# Должно быть видно 0.0.0.0:3000 и 0.0.0.0:8000
```

**На другой машине:**
```bash
# Замените <IP_WINDOWS> на IP адрес Windows хоста
curl http://<IP_WINDOWS>:3000
curl http://<IP_WINDOWS>:8000/health
```

---

## Режим разработки (Mock)

Для разработки UI/UX без реальных контейнеров используйте mock-режим:

```powershell
# Установите переменную окружения
$env:MOCK_SANDBOX="true"

# Запустите backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api.main:app --reload

# В другом терминале - frontend
cd frontend\web
npm install
npm start
```

**Или используйте скрипт:**
```powershell
.\scripts\start-dev-windows.bat
```

**В этом режиме работает:**
- ✅ Просмотр миссий
- ✅ Навигация по интерфейсу
- ✅ API запросы
- ✅ Система прогресса
- ✅ Проверка заданий (с mock-данными)
- ❌ Реальные контейнеры (требует Linux)

---

## Решение проблем

### PostgreSQL не запускается

```bash
# Проверьте, установлен ли PostgreSQL
psql --version

# Запустите вручную
sudo service postgresql start

# Проверьте логи
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

### Docker не работает

1. Убедитесь, что Docker Desktop запущен в Windows
2. Проверьте интеграцию WSL в настройках Docker Desktop
3. Перезапустите WSL: `wsl --shutdown` (в PowerShell), затем откройте снова

### Порт занят

```bash
# Проверьте, что использует порт
sudo lsof -i :8000
sudo lsof -i :3000
```

### Backend не отвечает

```bash
# Проверьте логи
tail -f backend.log

# Инициализируйте БД вручную
cd backend
source venv/bin/activate
python init_db.py
```

### Не могу подключиться с другой машины

1. **Проверьте брандмауэр Windows**:
   ```powershell
   Get-NetFirewallRule -DisplayName "*Astra Trainer*"
   ```

2. **Проверьте port forwarding** (если используете способ 2):
   ```powershell
   netsh interface portproxy show all
   ```

3. **Проверьте, что сервисы запущены**:
   ```bash
   ps aux | grep -E '(uvicorn|react-scripts)'
   ```

4. **Проверьте сетевые настройки**:
   - Убедитесь, что обе машины в одной локальной сети
   - Проверьте, что Windows не в режиме "Общедоступная сеть"

### После перезапуска WSL подключение не работает

- **Для Mirrored Networking Mode**: Просто перезапустите WSL (`wsl --shutdown` и откройте снова)
- **Для Port Forwarding**: Запустите скрипт `setup-wsl-port-forwarding.ps1` снова

---

## Ручная установка в WSL (если скрипт не работает)

### 1. Установка зависимостей

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nodejs npm postgresql postgresql-contrib git build-essential
```

### 2. Настройка PostgreSQL

```bash
sudo service postgresql start

sudo -u postgres psql << EOF
CREATE USER trainer_user WITH PASSWORD 'trainer_password';
CREATE DATABASE trainer_db OWNER trainer_user ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE trainer_db TO trainer_user;
\q
EOF
```

### 3. Настройка Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python init_db.py
```

### 4. Настройка Frontend

```bash
cd frontend/web
npm install
```

### 5. Запуск

```bash
# Backend (в одном терминале)
cd backend
source venv/bin/activate
python run.py

# Frontend (в другом терминале)
cd frontend/web
npm start
```

---

## Рекомендации

- **Для разработки UI/UX**: Используйте режим разработки на Windows
- **Для тестирования логики**: WSL2 с Docker
- **Для финального тестирования**: Реальная Linux система или виртуальная машина

---

## См. также

- [GETTING_STARTED.md](../GETTING_STARTED.md) - Полное руководство по установке
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение других проблем
