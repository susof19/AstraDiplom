# Разработка на Windows и WSL

Это руководство поможет вам установить и запустить Linux Training Simulator на Windows или в WSL (Windows Subsystem for Linux).

## Что можно тестировать на Windows

### ✅ Полностью работает на Windows:

1. **Frontend (React)**
   - Весь интерфейс
   - Навигация по миссиям
   - Взаимодействие с API
   - Запуск: `npm start`

2. **Backend API (FastAPI)**
   - Все API endpoints
   - Логика проверки заданий (Grader)
   - Система прогресса
   - Запуск: `python -m uvicorn api.main:app --reload`

3. **Логика приложения**
   - Управление миссиями
   - Проверка выполнения заданий
   - Система достижений

### ❌ Требует Linux:

1. **Podman/контейнеры**
   - Podman не работает нативно на Windows
   - Контейнеры Astra Linux требуют Linux

2. **Реальные песочницы**
   - Запуск контейнеров
   - VNC подключения
   - Терминалы в контейнерах

## Установка и запуск в WSL

### Быстрый старт в WSL

**Установка (один раз)**:
```bash
# В WSL терминале
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

### Предварительные требования для WSL

1. **WSL 2** установлен и настроен
   - Проверьте: `wsl --version` в PowerShell
   - Если не установлен: `wsl --install`

2. **Docker Desktop для Windows** (рекомендуется)
   - Скачайте: https://www.docker.com/products/docker-desktop
   - Установите и запустите Docker Desktop
   - Включите интеграцию с WSL в настройках Docker Desktop

### Особенности WSL

**PostgreSQL**:
В WSL PostgreSQL может не запускаться автоматически через `systemctl`. Скрипт использует `service` для запуска:
```bash
# Запуск PostgreSQL
sudo service postgresql start

# Проверка статуса
sudo service postgresql status
```

**Docker**:
Для работы с контейнерами рекомендуется использовать **Docker Desktop для Windows**:
1. Установите Docker Desktop
2. Включите интеграцию с WSL в настройках
3. Docker будет доступен в WSL автоматически

Проверка:
```bash
docker --version
docker info
```

**Сеть**:
- Frontend и Backend доступны на `localhost` как в WSL, так и в Windows
- Порт 3000 (Frontend) и 8000 (Backend) пробрасываются автоматически
- Откройте браузер Windows и перейдите на http://localhost:3000

**Доступ из локальной сети**:

WSL2 использует виртуальную сеть, поэтому для доступа из локальной сети требуется настройка. Есть два варианта:

### Вариант 1: Mirrored Networking Mode (Рекомендуется)

Это современное решение, которое делает WSL2 доступным из локальной сети без необходимости настройки port forwarding.

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

4. **Подключитесь с других машин**:
   - Узнайте IP адрес Windows хоста: `ipconfig | findstr IPv4` (в PowerShell)
   - Используйте: `http://<IP_АДРЕС_WINDOWS>:3000` для Frontend

### Вариант 2: Port Forwarding

Альтернативный вариант с ручной настройкой port forwarding.

1. **Настройка (требуется после каждого перезапуска WSL, если IP изменился)**:
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

**Примечание**: Оба скрипта автоматически настраивают Windows Firewall. Если используете port forwarding, запускайте скрипт после каждого перезапуска WSL, если IP адрес изменился.

### Доступ из локальной сети

**Важно**: WSL2 требует специальной настройки для доступа из локальной сети.

📖 **Подробное руководство**: [WSL_NETWORK_ACCESS.md](WSL_NETWORK_ACCESS.md)

**Краткая инструкция:**

1. **Рекомендуемый способ (Mirrored Networking Mode)**:
   ```powershell
   # PowerShell от имени администратора
   PowerShell -ExecutionPolicy Bypass -File scripts/setup-wsl-mirrored-networking.ps1
   wsl --shutdown  # Перезапустите WSL
   ```

2. **Альтернативный способ (Port Forwarding)**:
   ```powershell
   # PowerShell от имени администратора
   PowerShell -ExecutionPolicy Bypass -File scripts/setup-wsl-port-forwarding.ps1
   ```

3. Запустите приложение и используйте IP адрес Windows хоста для подключения.

### Устранение неполадок в WSL

**PostgreSQL не запускается**:
```bash
# Проверьте, установлен ли PostgreSQL
psql --version

# Запустите вручную
sudo service postgresql start

# Проверьте логи
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

**Docker не работает**:
1. Убедитесь, что Docker Desktop запущен в Windows
2. Проверьте интеграцию WSL в настройках Docker Desktop
3. Перезапустите WSL: `wsl --shutdown` (в PowerShell), затем откройте снова

**Порт занят**:
```bash
# Проверьте, что использует порт
sudo lsof -i :8000
sudo lsof -i :3000
```

**Backend не отвечает**:
Проверьте логи:
```bash
tail -f backend.log
```

Инициализируйте БД вручную:
```bash
cd backend
source venv/bin/activate
python init_db.py
```

## Варианты тестирования на Windows

### Вариант 1: WSL2 (Рекомендуется)

См. раздел [Установка и запуск в WSL](#установка-и-запуск-в-wsl) выше.

### Вариант 2: Режим разработки (Mock режим)

Используйте режим разработки без реальных контейнеров для тестирования логики:

```bash
# В backend/.env или через переменные окружения
MOCK_SANDBOX=true
```

В этом режиме:
- API работает, но не создаёт реальные контейнеры
- Можно тестировать весь UI и логику
- Проверка заданий работает с mock-данными

### Вариант 3: Виртуальная машина

Установите Astra Linux или Ubuntu в VirtualBox/VMware:
- Полная функциональность
- Реальные контейнеры
- Но медленнее, чем WSL2

### Вариант 4: Удалённый сервер

Разверните backend на удалённом Linux сервере:
- Frontend на Windows подключается к удалённому API
- Полная функциональность
- Требует настройки сети

## Быстрый старт для разработки на Windows

### 1. Установите зависимости

```powershell
# Python 3.10+
# Node.js 18+
# Git
```

### 2. Запустите в режиме разработки (без контейнеров)

**Терминал 1 - Backend:**
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Запуск с mock режимом
$env:MOCK_SANDBOX="true"
python -m uvicorn api.main:app --reload
```

**Терминал 2 - Frontend:**
```powershell
cd frontend\web
npm install
npm start
```

### 3. Что будет работать:

✅ Просмотр миссий
✅ Навигация по интерфейсу
✅ API запросы
✅ Система прогресса
✅ Проверка заданий (с mock-данными)
❌ Реальные контейнеры (требует Linux)

## Тестирование с реальными контейнерами

Для полного тестирования с контейнерами:

1. **Используйте WSL2** (самый простой вариант)
2. **Или установите Astra Linux в виртуальной машине**
3. **Или используйте удалённый Linux сервер**

## Ручная установка в WSL (если скрипт не работает)

### 1. Установка зависимостей

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nodejs npm postgresql postgresql-contrib git build-essential
```

### 2. Настройка PostgreSQL

```bash
# Запуск PostgreSQL
sudo service postgresql start

# Создание пользователя и базы данных с кодировкой UTF-8
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
deactivate
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

## Полезные команды для WSL

```bash
# Проверка статуса сервисов
sudo service postgresql status

# Просмотр логов PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-*-main.log

# Проверка подключения к БД
psql -h localhost -U trainer_user -d trainer_db

# Очистка и переустановка
rm -rf backend/venv frontend/web/node_modules
./scripts/quickstart-wsl.sh
```

## Рекомендации

- **Для разработки UI/UX**: Используйте режим разработки на Windows
- **Для тестирования логики**: WSL2 с Podman
- **Для финального тестирования**: Реальная Astra Linux или виртуальная машина

## Troubleshooting

### Podman не найден на Windows

Это нормально. Podman работает только в Linux. Используйте:
- WSL2 для локального тестирования
- Mock режим для разработки UI
- Удалённый сервер для полного тестирования

### Backend не запускается

Убедитесь, что:
- Python 3.10+ установлен
- Виртуальное окружение активировано
- Все зависимости установлены: `pip install -r requirements.txt`

### Frontend не подключается к API

Проверьте:
- Backend запущен на `http://localhost:8000`
- В `package.json` указан правильный proxy
- Нет ошибок CORS в консоли браузера

