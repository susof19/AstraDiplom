# Быстрый старт

## Минимальная установка (5 минут)

### 1. Установите зависимости

```bash
# Podman (rootless)
sudo apt-get install podman

# Python 3.10+
sudo apt-get install python3 python3-venv

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Клонируйте и установите

```bash
cd AstraDiplom

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend/web
npm install
```

### 3. Создайте образ Astra Linux

**Вариант A: Использование скрипта (рекомендуется для Astra Linux)**

```bash
cd scripts
sudo ./create-astra-image.sh
```

**Вариант B: Использование Dockerfile**

```bash
cd images
podman build -f Dockerfile.astra-gui -t astra-linux:latest .
```

**Примечание**: Для работы в Astra Linux Special Edition рекомендуется использовать скрипт `create-astra-image.sh`, который создаёт образ через debootstrap согласно официальной документации.

### 4. Запустите приложение

**Вариант 1: Автоматический запуск**
```bash
./scripts/start.sh
```

**Вариант 2: Ручной запуск**

Терминал 1 (Backend):

**Вариант A: Из корневой директории (рекомендуется)**
```bash
# Из корневой директории проекта
cd AstraDiplom
source backend/venv/bin/activate  # Linux/Mac
# или
backend\venv\Scripts\activate  # Windows

python -m backend.api.main
```

**Вариант B: Из директории backend (Windows)**
```bash
cd backend
venv\Scripts\activate
python run.py
```

**Вариант C: Через uvicorn из корня**
```bash
# Из корневой директории проекта
cd AstraDiplom
source backend/venv/bin/activate
uvicorn backend.api.main:app --reload
```

Терминал 2 (Frontend):
```bash
cd frontend/web
npm start
```

### 5. Откройте в браузере

http://localhost:3000

## Первая миссия

1. На главной странице выберите "Уровень A: Новички"
2. Выберите миссию "Копирование файла с USB"
3. Нажмите "Запустить песочницу"
4. Выполните задание
5. Нажмите "Проверить выполнение"

## Troubleshooting

### Podman не работает

```bash
# Проверка
podman info

# Если ошибка с socket
systemctl --user enable podman.socket
systemctl --user start podman.socket
```

### Backend не запускается

```bash
# Проверьте Python версию
python3 --version  # Должно быть 3.10+

# Переустановите зависимости
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend не подключается к API

- Убедитесь, что backend запущен на порту 8000
- Проверьте консоль браузера на ошибки CORS
- Проверьте `frontend/web/package.json` - поле `proxy` должно указывать на `http://localhost:8000`

## Следующие шаги

- Прочитайте [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) для понимания архитектуры
- Изучите [docs/MISSIONS.md](docs/MISSIONS.md) для создания новых миссий
- См. [docs/SETUP.md](docs/SETUP.md) для детальной настройки

