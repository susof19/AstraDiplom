# Astra Linux Training Simulator

Тренажёр для безопасного обучения работе с Astra Linux через практические задания в изолированных песочницах.

## 🎯 Основные возможности

- **Песочница per-mission**: Каждая задача выполняется в изолированной среде (контейнер Podman)
- **Три уровня сложности**:
  - **Уровень A**: GUI-first для новичков
  - **Уровень B**: CLI и скрипты для продвинутых
  - **Уровень C**: Инфраструктурные задачи для администраторов
- **Локальная версия**: Работа на устройстве пользователя (оффлайн)
- **Геймификация**: Миссии, уровни, достижения, прогресс
- **Адаптивные подсказки**: Rule-based система помощи при ошибках

## 🏗️ Архитектура

```
astra-trainer/
├── backend/              # Backend сервисы
│   ├── sandbox/         # Управление песочницами (Podman)
│   ├── grader/          # Проверка выполнения заданий
│   └── api/             # REST API
├── frontend/            # Веб-интерфейс
│   └── web/             # React приложение (Create React App)
├── missions/            # Определения миссий
│   ├── level_a/         # GUI-миссии
│   ├── level_b/         # CLI-миссии
│   └── level_c/         # Административные миссии
├── images/              # Dockerfile для образов Astra Linux
└── config/              # Конфигурационные файлы
```

## 🚀 Быстрый старт

### Для Astra Linux (рекомендуется)

Используйте автоматический скрипт установки:

```bash
cd AstraDiplom
chmod +x scripts/quickstart-astra.sh
./scripts/quickstart-astra.sh
```

Скрипт автоматически установит все зависимости и создаст ярлык для запуска.

См. [docs/ASTRA_LINUX.md](docs/ASTRA_LINUX.md) для подробностей.

### Для других Linux дистрибутивов

См. [QUICKSTART.md](QUICKSTART.md) для детальных инструкций.

### Минимальные требования

**Для полной функциональности:**
- **ОС**: Linux (Astra Linux, Ubuntu, Debian)
- **Python**: 3.10+
- **Podman**: последняя версия (rootless)
- **Node.js**: 18+

**Для разработки на Windows:**
- **ОС**: Windows 10/11
- **Python**: 3.10+
- **Node.js**: 18+
- **WSL2** (опционально, для тестирования с контейнерами)

### Быстрая установка

```bash
# 1. Установите зависимости (см. QUICKSTART.md)

# 2. Установите backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Установите frontend
cd ../frontend/web
npm install

# 4. Запустите (в двух терминалах)
# Терминал 1: Backend (из корневой директории)
source backend/venv/bin/activate  # Linux/Mac
# или backend\venv\Scripts\activate  # Windows
python -m backend.api.main
# или: uvicorn backend.api.main:app --reload

# Терминал 2: Frontend
cd frontend/web
npm start
```

Откройте http://localhost:3000 в браузере.

### Разработка на Windows (без Podman)

Для разработки на Windows можно использовать mock-режим:

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
npm start
```

Или используйте скрипт:
```powershell
.\scripts\start-dev-windows.bat
```

**Примечание**: В mock-режиме реальные контейнеры не создаются, но можно тестировать весь UI и логику приложения.

См. [docs/WINDOWS_DEVELOPMENT.md](docs/WINDOWS_DEVELOPMENT.md) для подробностей.

## 📋 Статус разработки

- ✅ MVP с локальной песочницей
- ✅ 10 миссий (5 уровня A, 3 уровня B, 2 уровня C)
- ✅ Система проверки заданий (Grader)
- ✅ Система прогресса и достижений
- 🚧 Интеграция VNC/терминала
- 🚧 Расширение набора миссий

## 🔒 Безопасность

- Rootless контейнеры (Podman) - соответствует требованиям Astra Linux
- Изоляция через overlayfs
- Поддержка меток безопасности (МКЦ) в Astra Linux
- Минимальные привилегии
- Совместимость с режимом изоляции Docker в Astra Linux

## 📚 Документация

### Быстрый старт
- [docs/ASTRA_LINUX.md](docs/ASTRA_LINUX.md) - **Установка и настройка на Astra Linux**
- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт для других систем
- [docs/WINDOWS_DEVELOPMENT.md](docs/WINDOWS_DEVELOPMENT.md) - Разработка на Windows

### Техническая документация
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Архитектура системы
- [docs/SETUP.md](docs/SETUP.md) - Детальная настройка
- [docs/MISSIONS.md](docs/MISSIONS.md) - Создание миссий

### Решение проблем
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - **Решение распространённых проблем**

### Дополнительно
- [CONTRIBUTING.md](CONTRIBUTING.md) - Руководство по вкладу

## 🎮 Текущие миссии

### Уровень A (5 миссий)
- Копирование файла с USB
- Создание ярлыка на рабочем столе
- Установка приложения из Software Center
- Изменение фона рабочего стола
- Организация файлов

### Уровень B (3 миссии)
- Создание архива логов
- Поиск процессов
- Скрипт резервного копирования

### Уровень C (2 миссии)
- Настройка firewall
- Создание systemd сервиса

## 🔧 Технологии

- **Backend**: FastAPI, Python 3.10+
- **Frontend**: React 18, Create React App
- **Sandbox**: Podman (rootless), LXC, QEMU
- **GUI**: XFCE, VNC (noVNC)
- **Terminal**: xterm.js

