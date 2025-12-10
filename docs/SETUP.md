# Руководство по установке

## Требования

### Системные требования

- **ОС**: Linux (рекомендуется Astra Linux или Ubuntu/Debian)
- **Python**: 3.10+
- **Node.js**: 18+
- **Podman**: последняя версия (rootless)

### Установка Podman (rootless)

```bash
# Ubuntu/Debian
sudo apt-get install -y podman

# Настройка rootless
podman system migrate
```

## Установка Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Установка Frontend

```bash
cd frontend/web
npm install
```

## Сборка образа Astra Linux

```bash
cd images
podman build -f Dockerfile.astra-gui -t astra-linux:latest .
```

**Примечание**: Для реального использования нужен официальный образ Astra Linux или его базовый образ.

## Запуск

### Backend

**Вариант 1: Из корневой директории проекта (рекомендуется)**
```bash
# Из корневой директории AstraDiplom
source backend/venv/bin/activate  # Linux/Mac
# или
backend\venv\Scripts\activate  # Windows

python -m backend.api.main
# или
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Вариант 2: Из директории backend (Windows)**
```bash
cd backend
venv\Scripts\activate
python run.py
```

### Frontend

```bash
cd frontend/web
npm start
```

Приложение будет доступно по адресу: http://localhost:3000

## Конфигурация

Настройки находятся в `backend/config.py`. Можно переопределить через переменные окружения:

```bash
export PODMAN_BINARY="podman"
export API_PORT=8000
export SANDBOX_MEMORY_LIMIT="2G"
```

## Проверка работы

1. Откройте http://localhost:3000
2. Выберите миссию уровня A
3. Нажмите "Запустить песочницу"
4. Выполните задание
5. Нажмите "Проверить выполнение"

## Troubleshooting

### Podman не запускается

```bash
# Проверка статуса
podman info

# Перезапуск службы
systemctl --user restart podman.socket
```

### Контейнеры не создаются

- Проверьте права доступа к Podman socket
- Убедитесь, что образ `astra-linux:latest` существует
- Проверьте логи: `podman logs <container_name>`

### Frontend не подключается к API

- Проверьте, что backend запущен на порту 8000
- Проверьте настройки CORS в `backend/config.py`
- Проверьте proxy в `frontend/web/package.json` (поле `proxy`)

