# Разработка на Windows

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

## Варианты тестирования на Windows

### Вариант 1: WSL2 (Рекомендуется)

Установите WSL2 с Ubuntu/Debian и используйте его для запуска Podman:

```bash
# В WSL2
wsl --install -d Ubuntu

# В WSL2 установите Podman
sudo apt update
sudo apt install podman

# Запустите backend в WSL2
cd /mnt/z/PyProjects/AstraDiplom/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --host 0.0.0.0
```

Frontend запускайте в Windows PowerShell:
```powershell
cd frontend\web
npm start
```

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

