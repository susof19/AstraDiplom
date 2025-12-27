# Linux Training Simulator

Тренажёр для безопасного обучения работе с Linux через практические задания в изолированных песочницах. Поддерживает любые Debian-based дистрибутивы (Debian, Ubuntu, Astra Linux, Linux Mint и др.).

## 🎯 Основные возможности

- **Песочница per-mission**: Каждая задача выполняется в изолированной среде (контейнер Podman/Docker)
- **Три уровня сложности**:
  - **Уровень A**: GUI-first для новичков (с VNC через браузер)
  - **Уровень B**: CLI и скрипты для продвинутых
  - **Уровень C**: Инфраструктурные задачи для администраторов
- **Система аутентификации**: Регистрация, вход, восстановление пароля по секретному коду
- **Локальная версия**: Работа на устройстве пользователя (оффлайн)
- **Геймификация**: Миссии, уровни, достижения, прогресс
- **Адаптивные подсказки**: Rule-based система помощи при ошибках
- **Кроссплатформенность**: Работает на любой Debian-based системе

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
│   └── level_a/         # GUI-миссии
├── images/              # Dockerfile для образов Astra Linux
└── config/              # Конфигурационные файлы
```

## 🚀 Быстрый старт

### Автоматическая установка (Linux)

```bash
cd AstraDiplom
chmod +x scripts/quickstart.sh
./scripts/quickstart.sh
```

Скрипт автоматически определит ваш дистрибутив и установит все зависимости.

### Минимальные требования

- **ОС**: Linux (Debian, Ubuntu, Astra Linux и другие Debian-based дистрибутивы) или Windows с WSL2
- **Python**: 3.10+
- **Podman или Docker**: последняя версия
- **Node.js**: 18+

### Установка на Windows

Для разработки на Windows используйте WSL2 или mock-режим. Подробности: [docs/WINDOWS_DEVELOPMENT.md](docs/WINDOWS_DEVELOPMENT.md)

**Полное руководство по установке**: [GETTING_STARTED.md](GETTING_STARTED.md)

## 📋 Статус разработки

- ✅ MVP с локальной песочницей
- ✅ 10 миссий (5 уровня A, 3 уровня B, 2 уровня C)
- ✅ Система проверки заданий (Grader)
- ✅ Система прогресса и достижений
- ✅ Интеграция VNC для GUI-миссий (TigerVNC + noVNC)
- ✅ Автоматический запуск VNC в контейнерах
- ✅ Система аутентификации (регистрация, вход, восстановление пароля)
- ✅ Совместимость с любыми Debian-based системами
- 🚧 Интеграция терминала (xterm.js)
- 🚧 Расширение набора миссий

## 🔒 Безопасность

- Rootless контейнеры (Podman)
- Минимальные привилегии
- Совместимость с режимом изоляции Docker 

## 📚 Документация

### 🚀 Начало работы
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - Полное руководство по установке и использованию
- **[DEMO_GUIDE.md](DEMO_GUIDE.md)** - Руководство для демонстрации на дипломе
- **[AUTHENTICATION.md](AUTHENTICATION.md)** - Система аутентификации и регистрации

### Установка на разных системах
- [GETTING_STARTED.md](GETTING_STARTED.md) - Полное руководство по установке (включая Astra Linux)
- [docs/WINDOWS_DEVELOPMENT.md](docs/WINDOWS_DEVELOPMENT.md) - Разработка на Windows и WSL (включая доступ из локальной сети)

### Руководства по компонентам
- [docs/PODMAN_GUIDE.md](docs/PODMAN_GUIDE.md) - Работа с Podman и создание образов
- [docs/VNC_GUIDE.md](docs/VNC_GUIDE.md) - VNC для GUI-миссий через браузер (включая настройку Astra Linux VNC)
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Решение проблем (Backend, БД, образы, VNC, сеть)

### Техническая документация
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Архитектура системы (компоненты, образы, API)
- [docs/MISSIONS.md](docs/MISSIONS.md) - Создание миссий
- [scripts/README.md](scripts/README.md) - Документация скриптов и настройка дистрибутивов

### Разработка
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

