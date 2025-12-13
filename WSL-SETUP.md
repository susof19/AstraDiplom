# Установка и запуск на WSL (Windows Subsystem for Linux)

Это руководство поможет вам установить и запустить Linux Training Simulator в WSL.

## Предварительные требования

1. **WSL 2** установлен и настроен
   - Проверьте: `wsl --version` в PowerShell
   - Если не установлен: `wsl --install`

2. **Docker Desktop для Windows** (рекомендуется)
   - Скачайте: https://www.docker.com/products/docker-desktop
   - Установите и запустите Docker Desktop
   - Включите интеграцию с WSL в настройках Docker Desktop

## Быстрая установка

1. Откройте WSL терминал

2. Перейдите в директорию проекта:
   ```bash
   cd /path/to/AstraDiplom
   ```

3. Запустите скрипт установки:
   ```bash
   chmod +x scripts/quickstart-wsl.sh
   ./scripts/quickstart-wsl.sh
   ```

Скрипт автоматически:
- Установит все зависимости (Python, Node.js, PostgreSQL)
- Настроит виртуальное окружение
- Установит зависимости backend и frontend
- Настроит базу данных PostgreSQL
- Создаст скрипт запуска `start-demo-wsl.sh`

## Запуск приложения

После установки запустите:

```bash
./start-demo-wsl.sh
```

Приложение будет доступно:
- **Frontend**: http://localhost:3000 (откройте в браузере Windows)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Остановка приложения

```bash
./stop-demo.sh
```

Или вручную:
```bash
kill $(cat .backend.pid) $(cat .frontend.pid)
```

## Особенности WSL

### PostgreSQL

В WSL PostgreSQL может не запускаться автоматически через `systemctl`. Скрипт использует `service` для запуска:

```bash
# Запуск PostgreSQL
sudo service postgresql start

# Проверка статуса
sudo service postgresql status

# Остановка
sudo service postgresql stop
```

Если `service` не работает, запустите вручную:
```bash
sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/*/main start
```

### Docker

Для работы с контейнерами рекомендуется использовать **Docker Desktop для Windows**:

1. Установите Docker Desktop
2. Включите интеграцию с WSL в настройках
3. Docker будет доступен в WSL автоматически

Проверка:
```bash
docker --version
docker info
```

### Сеть

- Frontend и Backend доступны на `localhost` как в WSL, так и в Windows
- Порт 3000 (Frontend) и 8000 (Backend) пробрасываются автоматически
- Откройте браузер Windows и перейдите на http://localhost:3000

## Устранение неполадок

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

Если порт 3000 или 8000 занят:

```bash
# Проверьте, что использует порт
sudo lsof -i :8000
sudo lsof -i :3000

# Остановите процесс или измените порт в config.py
```

### Backend не отвечает

Проверьте логи:
```bash
tail -f backend.log
```

Убедитесь, что:
- PostgreSQL запущен
- База данных создана: `trainer_db`
- Пользователь создан: `trainer_user`

Инициализируйте БД вручную:
```bash
cd backend
source venv/bin/activate
python init_db.py
```

### Frontend не открывается

1. Проверьте, что frontend запущен: `tail -f frontend.log`
2. Убедитесь, что порт 3000 не занят
3. Проверьте proxy настройки в `frontend/web/src/setupProxy.js`

## Ручная установка (если скрипт не работает)

### 1. Установка зависимостей

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nodejs npm postgresql postgresql-contrib git build-essential
```

### 2. Настройка PostgreSQL

```bash
# Запуск PostgreSQL
sudo service postgresql start

# Создание пользователя и базы данных
sudo -u postgres psql << EOF
CREATE USER trainer_user WITH PASSWORD 'trainer_password';
CREATE DATABASE trainer_db OWNER trainer_user;
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

## Полезные команды

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

## Дополнительная информация

- Логи backend: `tail -f backend.log`
- Логи frontend: `tail -f frontend.log`
- API документация: http://localhost:8000/docs
- Health check: http://localhost:8000/health

