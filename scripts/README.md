# Скрипты Astra Linux Training Simulator

## Основные скрипты

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
- Базовый: `localhost/astra-linux:se`
- С VNC: `localhost/astra-linux:vnc`

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

```
localhost/astra-linux:se    - Базовый образ (Astra Linux + CLI)
localhost/astra-linux:vnc   - Образ с VNC (+ TigerVNC + noVNC + XFCE)
```

---

## Дополнительная информация

- **Podman**: [docs/PODMAN_GUIDE.md](../docs/PODMAN_GUIDE.md)
- **VNC**: [docs/VNC_GUIDE.md](../docs/VNC_GUIDE.md)
- **Решение проблем**: [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)
