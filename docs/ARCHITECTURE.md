# Архитектура Linux Training Simulator

## Обзор

Linux Training Simulator — это универсальная платформа для обучения работе с Linux, поддерживающая различные Debian-based дистрибутивы (Debian, Ubuntu, Astra Linux).

Тренажёр состоит из трёх основных компонентов:

1. **Backend (FastAPI)** - управление песочницами, проверка заданий, API
2. **Frontend (React)** - веб-интерфейс для пользователей
3. **Sandbox (Podman/Docker)** - изолированные контейнеры с Linux

---

## Компоненты системы

### Backend (FastAPI)

#### Sandbox Manager

Управляет жизненным циклом контейнеров:
- Создание/удаление контейнеров для каждой миссии
- Автоматическая очистка истёкших песочниц
- Изоляция через rootless Podman или Docker
- Автоматический выбор образа по дистрибутиву и уровню

#### Grader

Проверяет выполнение заданий:
- Загружает конфигурацию миссии (YAML)
- Выполняет проверки (файлы, команды, GUI-состояние)
- Возвращает результат с оценкой

#### Progress System

Отслеживает прогресс пользователя:
- Завершённые миссии и оценки
- Достижения (achievements)
- Статистика по уровням

#### API Endpoints

**Missions:**
- `GET /api/v1/missions` - список миссий
- `GET /api/v1/missions/{id}` - информация о миссии

**Sandbox:**
- `POST /api/v1/sandbox/create` - создать песочницу
- `GET /api/v1/sandbox/{mission_id}` - информация о песочнице
- `POST /api/v1/sandbox/{mission_id}/stop` - остановить
- `DELETE /api/v1/sandbox/{mission_id}` - удалить

**Grader:**
- `POST /api/v1/grader/check/{mission_id}` - проверить выполнение

**Progress:**
- `GET /api/v1/progress` - прогресс пользователя
- `POST /api/v1/progress/{mission_id}/complete` - отметить выполненной
- `GET /api/v1/progress/achievements` - достижения

**Auth:**
- `POST /api/v1/auth/register` - регистрация
- `POST /api/v1/auth/login` - вход
- `GET /api/v1/auth/me` - информация о текущем пользователе

### Frontend (React)

Веб-интерфейс для пользователей:
- React 18 с Create React App
- React Query для управления состоянием
- Аутентификация через JWT токены
- VNC интеграция через noVNC для GUI-миссий
- Терминал через xterm.js для CLI-миссий (планируется)

---

## Многоуровневая модель образов

Проект использует многоуровневую архитектуру Docker-образов для обеспечения гибкости и переиспользования:

### 🧱 Базовые образы (CLI)

Базовые образы содержат только командную строку, без GUI:

| Образ | Описание | Базовый образ |
|-------|----------|---------------|
| `linux-base:debian` | Debian 12 CLI | `debian:12` |
| `linux-base:ubuntu` | Ubuntu 22.04 CLI | `ubuntu:22.04` |
| `linux-base:astra` | Astra Linux SE CLI | `astra-linux:se` (требует debootstrap) |

**Использование:**
- Уровни B и C (терминальные миссии)
- Минимальный размер образа
- Быстрый запуск

### 🖥 GUI-надстройка (VNC)

GUI-образы добавляют графический интерфейс и VNC:

| Образ | Описание | FROM |
|-------|----------|-----|
| `linux-gui-vnc:debian` | Debian 12 с XFCE + VNC | `linux-base:debian` |
| `linux-gui-vnc:ubuntu` | Ubuntu 22.04 с XFCE + VNC | `linux-base:ubuntu` |
| `linux-gui-vnc:astra` | Astra Linux SE с XFCE + VNC | `linux-base:astra` |
| `astra-vnc:latest` | Готовый образ из репозитория (опционально) | `astra-fly:v1.7.6` |

**Компоненты:**
- XFCE Desktop Environment
- TigerVNC Server
- noVNC (веб-клиент VNC)
- websockify (из git, без pip)

**Использование:**
- Уровень A (GUI миссии)
- Веб-доступ через браузер

### 🎯 Миссионные образы (опционально)

В будущем можно добавить специализированные образы для конкретных миссий:

| Образ | Описание | FROM |
|-------|----------|-----|
| `trainer-level-a` | Предустановленные инструменты для уровня A | `linux-gui-vnc:*` |

---

## Структура файлов

```
images/
├── Dockerfile.gui-vnc          # Универсальный GUI образ (заменяет Dockerfile.astra-vnc)
├── Dockerfile.base             # Базовый CLI образ
├── supervisord.conf            # Конфигурация supervisor для VNC
├── start-vnc.sh                # Скрипт запуска VNC
└── ...
```

---

## Выбор дистрибутива

### Backend конфигурация

В `backend/config.py` определены маппинги дистрибутивов:

```python
DEFAULT_DISTRO: str = "debian"  # По умолчанию

DISTRO_GUI_IMAGES: dict[str, str] = {
    "debian": "localhost/linux-gui-vnc:debian",
    "ubuntu": "localhost/linux-gui-vnc:ubuntu",
    "astra": "localhost/astra-vnc:latest"  # Или localhost/linux-gui-vnc:astra
}

DISTRO_BASE_CLI_IMAGES: dict[str, str] = {
    "debian": "localhost/linux-base:debian",
    "ubuntu": "localhost/linux-base:ubuntu",
    "astra": "localhost/linux-base:astra"
}
```

### Автоматический выбор образа

`ContainerSandbox` автоматически выбирает образ на основе:
- **Уровня миссии** (A = GUI, B/C = CLI)
- **Дистрибутива** (debian/ubuntu/astra)
- **Настройки VNC** (use_vnc)

### API

```python
POST /api/v1/sandbox/create
{
    "mission_id": "mission-1",
    "level": "A",
    "distro": "debian",  # Опционально: debian, ubuntu, astra
    "use_vnc": true
}
```

---

## Уровни миссий

| Уровень | GUI | Образ | Описание |
|---------|-----|-------|----------|
| A | ✅ | `linux-gui-vnc:*` | Графический интерфейс через VNC (noVNC в браузере) |
| B | ❌ | `linux-base:*` | Терминальные команды (xterm.js планируется) |
| C | ❌ | `linux-base:*` | Продвинутые административные команды |

### Уровень A (GUI-first)

- **Песочница**: Rootless Podman/Docker + XFCE + VNC
- **Интерфейс**: noVNC в браузере
- **Примеры миссий**: Копирование файлов, создание ярлыков, установка приложений

### Уровень B (CLI & Scripting)

- **Песочница**: Rootless Podman/Docker с терминалом
- **Интерфейс**: xterm.js в браузере (планируется)
- **Примеры миссий**: Создание архивов, поиск процессов, bash-скрипты

### Уровень C (Администраторы)

- **Песочница**: Podman/Docker контейнеры или LXC/systemd-nspawn
- **Интерфейс**: Терминал + веб-панель управления
- **Примеры миссий**: Настройка systemd, firewall, кластеры

---

## Формат миссий

Миссии описываются в YAML:

```yaml
name: "Название миссии"
description: "Описание задания"
level: "A"  # Уровень A (GUI-миссии)
difficulty: 1-5
estimated_time: 10  # минут

objectives:
  - "Цель 1"
  - "Цель 2"

hints:
  - "Подсказка 1"

checks:
  - name: "Проверка 1"
    type: "file_exists"
    path: "/path/to/file"
    points: 50
```

---

## Безопасность

- **Rootless контейнеры**: Все контейнеры запускаются без root-прав (Podman rootless или Docker)
- **Изоляция**: OverlayFS для отката изменений
- **Ограничения ресурсов**: CPU и память ограничены
- **Автоудаление**: Контейнеры удаляются после завершения
- **Минимальные привилегии**: Контейнеры имеют только необходимые права

---

## Сборка образов

### GUI образ (универсальный)

```bash
# Debian
docker build -f images/Dockerfile.gui-vnc \
    --build-arg BASE_IMAGE=debian:12 \
    -t localhost/linux-gui-vnc:debian .

# Ubuntu
docker build -f images/Dockerfile.gui-vnc \
    --build-arg BASE_IMAGE=ubuntu:22.04 \
    -t localhost/linux-gui-vnc:ubuntu .

# Astra Linux (требует предварительно собранный astra-linux:se)
docker build -f images/Dockerfile.gui-vnc \
    --build-arg BASE_IMAGE=astra-linux:se \
    -t localhost/linux-gui-vnc:astra .
```

Или используйте скрипт:

```bash
./scripts/create-astra-image.sh --vnc
```

---

## Ключевые принципы

### ✅ Универсальность

- **Нет хардкода дистрибутивов** в Dockerfile
- Использование `ARG BASE_IMAGE` для выбора базового образа
- Все команды работают на любом Debian-based дистрибутиве

### ✅ Минимальные зависимости

- **websockify из git**, не из pip (избегаем проблем с зависимостями)
- Минимальный набор пакетов
- Опциональная установка (fallback на альтернативы)

### ✅ Обратная совместимость

- Старый код с `image="localhost/astra-linux:se"` продолжит работать
- Автоматический выбор образа, если не указан явно
- Поддержка legacy имен образов

---

## Развитие архитектуры

### Текущее состояние

- ✅ Универсальный GUI Dockerfile
- ✅ Автоматический выбор образа по дистрибутиву
- ✅ Поддержка Debian, Ubuntu, Astra Linux
- ✅ VNC через noVNC (веб-доступ)
- ✅ PostgreSQL для хранения данных пользователей
- ✅ JWT аутентификация

### Планы на будущее

- [ ] Базовые CLI образы (`Dockerfile.base`)
- [ ] Специализированные миссионные образы
- [ ] Кэширование образов для быстрого запуска
- [ ] Поддержка других дистрибутивов (Fedora, CentOS)
- [ ] VM-уровень для уровня C (LXC/KVM)
- [ ] Интеграция xterm.js для терминала в браузере
- [ ] Расширенная система достижений

---

## Решение проблем

### Ошибки dbus в логах

Ошибки `dbus exited (exit status 1)` не критичны:
- dbus запускается через `dbus-launch` внутри VNC-сессии
- Отдельный системный dbus не требуется
- VNC работает корректно

### Проброс портов в WSL

Используется явное указание `0.0.0.0`:
```python
"-p", f"0.0.0.0:{self.vnc_port}:5900"
```

Это позволяет подключаться к портам контейнера из WSL.

### Автоматическая адаптация портов

Код автоматически определяет тип образа и настраивает порты:
- `astra-vnc:latest` использует порт 80 для noVNC
- Остальные образы используют порт 6080 для noVNC
- VNC всегда на порту 5900

---

## Документация для диплома

### Ключевые моменты для презентации

1. **Архитектурная универсальность**: один Dockerfile для всех дистрибутивов
2. **Многоуровневая модель**: разделение базовых и GUI образов
3. **Автоматический выбор**: система сама выбирает нужный образ
4. **Расширяемость**: легко добавить новые дистрибутивы
5. **Безопасность**: rootless контейнеры, изоляция, ограничения ресурсов

### Демонстрация

1. Показать работу с Debian (базовый случай)
2. Показать работу с Astra Linux (специфичный случай)
3. Показать автоматический выбор образа
4. Показать веб-доступ через noVNC
5. Показать систему миссий и проверки

---

## Дополнительная информация

- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [VNC Guide](VNC_GUIDE.md)
- [Podman Guide](PODMAN_GUIDE.md)
- [Missions Guide](MISSIONS.md)
