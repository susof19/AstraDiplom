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

**Результат**: Образ `localhost/astra-vnc:latest` готов к использованию.

**Подробнее**: [docs/VNC_GUIDE.md](../docs/VNC_GUIDE.md)

---

### 🔧 fix-podman-images.sh - Исправление проблем с образами

Переносит образы из root в rootless хранилище.

**Когда использовать**: Если образ создан через sudo, но не виден при `podman images`.

**Использование**:
```bash
./fix-podman-images.sh
```

---

### 📥 Работа с образами

**Импорт образа из tar-архива**:
```bash
./import-astra-image.sh /path/to/image.tar
```

**Загрузка образа из реестра**:
```bash
./pull-astra-image.sh
```

---

### 🎯 quickstart-*.sh - Быстрый старт

Автоматическая установка всех зависимостей для разных систем:

- `quickstart.sh` - для Linux (Debian, Ubuntu)
- `quickstart-astra.sh` - для Astra Linux
- `quickstart-wsl.sh` - для WSL

**Использование**:
```bash
./quickstart.sh          # Linux
./quickstart-astra.sh    # Astra Linux
./quickstart-wsl.sh      # WSL
```

Устанавливают:
- Podman/Docker
- Node.js
- Python зависимости
- Создают образы (опционально)
- Создают скрипты запуска

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

# Проверка базы данных
./check-database.sh

# Настройка базы данных
./setup-database.sh

# Исправление кодировки БД
./fix-database-encoding.sh
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

Система автоматически выбирает образ на основе уровня миссии и дистрибутива:
- **Уровень A** → `linux-gui-vnc:{distro}`
- **Уровни B/C** → `linux-base:{distro}`

В `backend/config.py` можно изменить дистрибутив по умолчанию:
```python
DEFAULT_DISTRO: str = "debian"  # debian, ubuntu, или astra
```

**Подробнее**: [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)

---

## Скрипты запуска

**start-demo.sh** - Запуск для Linux
- Проверяет наличие образов
- Запускает backend и frontend

**start-demo-wsl.sh** - Запуск для WSL
- Выбор образа для использования
- Запускает backend и frontend

## Обратная совместимость

Backend автоматически поддерживает старые имена образов:
- `localhost/astra-linux:se`
- `localhost/astra-linux:vnc`
- `localhost/linux-sandbox:base`
- `localhost/linux-sandbox:vnc`

---

## Решение проблем

**Образ не найден**: Убедитесь, что образ собран: `podman images` или `docker images`

**Образ не виден после создания через sudo**: Используйте `./fix-podman-images.sh`

**Проблемы с базой данных**: Используйте `./check-database.sh` и `./setup-database.sh`

**Подробнее**: [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)

---

## Дополнительная информация

- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - Архитектура системы
- [docs/PODMAN_GUIDE.md](../docs/PODMAN_GUIDE.md) - Работа с Podman
- [docs/VNC_GUIDE.md](../docs/VNC_GUIDE.md) - Настройка VNC
- [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md) - Решение проблем
