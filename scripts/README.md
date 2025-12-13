# Скрипты Astra Linux Training Simulator

## Основные скрипты

### 🔍 check-setup.sh - Проверка готовности

Проверяет наличие всех необходимых файлов и зависимостей.

**Использование**:
```bash
./check-setup.sh
```

Проверяет:
- Установку Podman
- Наличие Dockerfile и скриптов
- Доступность реестра Astra Linux
- Существующие образы
- Количество миссий

---

### 🚀 create-astra-image.sh - Создание образов

Универсальный скрипт для создания образов Astra Linux.

**Использование**:
```bash
./create-astra-image.sh [OPTIONS]
```

**Опции**:
- `--vnc` - Создать образ с VNC поддержкой (GUI)
- `--no-vnc` - Создать базовый образ (CLI) [по умолчанию]
- `--rootless` - Использовать rootless режим [по умолчанию]
- `--with-sudo` - Использовать sudo (debootstrap)
- `--help` - Показать справку

**Примеры**:
```bash
# Базовый образ для CLI-миссий (уровни B, C)
./create-astra-image.sh

# Образ с VNC для GUI-миссий (уровень A)
./create-astra-image.sh --vnc
```

**Результат**:
- Базовый: `localhost/linux-base:astra`
- С VNC: `localhost/linux-gui-vnc:astra` или `localhost/astra-vnc:latest` (из репозитория)

---

### 🔧 setup-astra-vnc-image.sh - Настройка образа Astra Linux с VNC

Настраивает готовый образ Astra Linux с VNC из репозитория [shinbatsu/astra-ui-vnc-container](https://github.com/shinbatsu/astra-ui-vnc-container).

**Использование**:
```bash
./setup-astra-vnc-image.sh
```

**Что делает**:
- Клонирует репозиторий с образом
- Собирает Docker/Podman образ `localhost/astra-vnc:latest`
- Подготавливает образ к использованию

**Результат**: Образ `localhost/astra-vnc:latest` готов к использованию для дистрибутива `astra`.

**Подробнее**: См. [ASTRA-VNC-SETUP.md](./ASTRA-VNC-SETUP.md)

---

### 🔧 fix-podman-images.sh - Исправление проблем

Переносит образы из root в rootless хранилище.

**Когда использовать**: Если образ создан через sudo, но не виден при `podman images`.

**Использование**:
```bash
./fix-podman-images.sh
```

---

### 📥 import-astra-image.sh - Импорт образа

Импортирует образ из tar-архива.

**Использование**:
```bash
./import-astra-image.sh /path/to/image.tar
```

---

### 📦 pull-astra-image.sh - Загрузка из реестра

Загружает готовый образ из реестра Astra Linux.

**Использование**:
```bash
./pull-astra-image.sh
```

---

### 🎯 quickstart-astra.sh - Быстрый старт

Автоматическая установка всех зависимостей на Astra Linux.

**Использование**:
```bash
./quickstart-astra.sh
```

Устанавливает:
- Podman
- Node.js
- Python зависимости
- Создаёт образы
- Создаёт ярлык запуска

---

### 🖥️ start.sh - Запуск приложения

Запускает backend и frontend (Linux/Mac).

**Использование**:
```bash
./start.sh
```

---

### 💻 start-dev-windows.bat - Запуск на Windows

Запускает приложение в mock-режиме на Windows.

**Использование**:
```powershell
.\start-dev-windows.bat
```

---

## Быстрые команды

### Создание образов

```bash
# Базовый образ (CLI)
./create-astra-image.sh

# Образ с VNC (GUI)
./create-astra-image.sh --vnc
```

### Проверка образов

```bash
# Список образов
podman images

# Тестовый запуск базового
podman run --rm -it localhost/astra-linux:se /bin/bash

# Тестовый запуск VNC
podman run -d -p 5900:5900 -p 6080:6080 localhost/astra-linux:vnc
# Откройте: http://localhost:6080/vnc.html
```

### Решение проблем

```bash
# Образ не виден после создания через sudo
./fix-podman-images.sh

# Проверка образов у root
sudo podman images

# Проверка образов у пользователя
podman images
```

---

## Структура образов

### Новые имена образов (рекомендуется)

```
localhost/linux-base:{distro}     - Базовый образ (CLI)
localhost/linux-gui-vnc:{distro}  - Образ с VNC (+ TigerVNC + noVNC + XFCE)
```

Где `{distro}` может быть: `debian`, `ubuntu`, `astra`

Примеры:
- `localhost/linux-base:debian` - Базовый Debian CLI
- `localhost/linux-gui-vnc:debian` - Debian с GUI
- `localhost/linux-gui-vnc:astra` - Astra Linux с GUI
- `localhost/astra-vnc:latest` - Готовый образ из репозитория shinbatsu/astra-ui-vnc-container

**Примечание**: Для Astra Linux рекомендуется использовать готовый образ `localhost/astra-vnc:latest` из репозитория, который уже настроен и протестирован.

### Legacy имена (для обратной совместимости)

Старые имена образов продолжают работать:
- `localhost/astra-linux:se`
- `localhost/astra-linux:vnc`
- `localhost/linux-sandbox:base`
- `localhost/linux-sandbox:vnc`

---

## Настройка дистрибутивов

### Использование в API

#### Автоматический выбор (рекомендуется)

```python
POST /api/v1/sandbox/create
{
    "mission_id": "mission-1",
    "level": "A",
    "distro": "debian"  # debian, ubuntu, или astra
}
```

Система автоматически выберет нужный образ:
- **Уровень A** → `linux-gui-vnc:{distro}`
- **Уровни B/C** → `linux-base:{distro}`

#### Явное указание образа

```python
POST /api/v1/sandbox/create
{
    "mission_id": "mission-1",
    "level": "A",
    "image": "localhost/linux-gui-vnc:debian"
}
```

### Настройка по умолчанию

В `backend/config.py` можно изменить дистрибутив по умолчанию:

```python
DEFAULT_DISTRO: str = "debian"  # Измените на ubuntu или astra
```

### Проверка образов

```bash
# Список всех образов
docker images | grep "linux-gui-vnc\|linux-base"
# или
podman images | grep "linux-gui-vnc\|linux-base"

# Проверка конкретного образа
docker images localhost/linux-gui-vnc:debian
```

### Сборка образов для разных дистрибутивов

#### Через скрипт (рекомендуется)

```bash
cd scripts
./create-astra-image.sh --vnc
# Выберите нужный вариант (Debian/Ubuntu/Astra)
```

#### Ручная сборка

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

---

## Совместимость скриптов

Все скрипты обновлены и работают с новой архитектурой образов.

### ✅ Работающие скрипты

**start-demo.sh** ✅
- Обновлен для поддержки новой схемы именования
- Проверяет наличие образов (старые и новые имена)

**start-demo-wsl.sh** ✅
- Работает без изменений
- Только запускает backend и frontend

**create-astra-image.sh** ✅
- Обновлен для создания образов с новой схемой именования
- Создает legacy теги для обратной совместимости

**Скрипты базы данных** ✅
- `setup-database.sh` - создание БД
- `check-database.sh` - проверка БД
- Не зависят от образов контейнеров

**Скрипты быстрого старта** ✅
- `quickstart.sh` - для Linux
- `quickstart-wsl.sh` - для WSL
- `quickstart-astra.sh` - для Astra Linux

### Обратная совместимость

Backend автоматически поддерживает старые имена:
- `localhost/astra-linux:se`
- `localhost/astra-linux:vnc`
- `localhost/linux-sandbox:base`
- `localhost/linux-sandbox:vnc`

Если вы явно указали старое имя образа в API, оно будет работать.

### Миграция со старых образов

Если у вас есть старые образы:

```bash
# Переименовать старый образ в новый формат
docker tag localhost/astra-linux:vnc localhost/linux-gui-vnc:astra
docker tag localhost/astra-linux:se localhost/linux-base:astra

# Или просто использовать старые имена - они продолжат работать
```

---

## Решение проблем

### Образ не найден

Если при создании песочницы возникает ошибка "image not found":
1. Убедитесь, что образ собран: `docker images` или `podman images`
2. Проверьте имя образа в `backend/config.py`
3. Пересоберите образ с правильным тегом

### Ошибки при сборке

**Проблема с websockify:**
- ✅ Исправлено: websockify теперь устанавливается только из git
- Убедитесь, что используете обновленный Dockerfile

**Проблема с dbus:**
- Ошибки dbus в логах не критичны
- VNC работает корректно, dbus запускается внутри VNC-сессии

### Проблемы с видимостью образов Podman

См. раздел "Проблемы с видимостью образов Podman" в [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)

---

## Дополнительная информация

- **Архитектура**: [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- **Podman**: [docs/PODMAN_GUIDE.md](../docs/PODMAN_GUIDE.md)
- **VNC**: [docs/VNC_GUIDE.md](../docs/VNC_GUIDE.md)
- **Решение проблем**: [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)
- **Настройка Astra VNC**: [ASTRA-VNC-SETUP.md](ASTRA-VNC-SETUP.md)
