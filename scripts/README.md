# Скрипты для работы с Astra Linux Training Simulator

## Создание образов

### 🚀 Рекомендуемый способ (rootless, без sudo)

```bash
./create-astra-image-rootless.sh
```

**Преимущества:**
- ✅ Не требует sudo
- ✅ Загружает готовый образ из реестра Astra Linux
- ✅ Быстрее работает
- ✅ Правильно работает с rootless podman
- ✅ Нет проблем с видимостью образов

**Использует**: Официальный образ `registry.astralinux.ru/library/astra/ubi18`

---

### 🔨 Альтернативный способ (через debootstrap, требует sudo)

```bash
sudo ./create-astra-image.sh
```

**Особенности:**
- ⚠️ Требует sudo
- ⚠️ Создаёт образ через debootstrap (медленнее)
- ⚠️ Образ создаётся в root-контексте
- ⚠️ Требует переноса в rootless-контекст

**После создания через sudo выполните:**
```bash
./fix-podman-images.sh
```

---

## Исправление проблем

### 🔧 Перенос образа из root в rootless

Если образ создан через sudo, но не виден при `podman images`:

```bash
./fix-podman-images.sh
```

Скрипт автоматически:
1. Экспортирует образ из root podman
2. Импортирует в rootless podman текущего пользователя
3. Правильно тегирует образ

---

## Быстрый старт

### Для Astra Linux (автоматическая установка)

```bash
./quickstart-astra.sh
```

Устанавливает все зависимости и создаёт ярлык для запуска.

---

## Другие скрипты

### `build-image.sh`
Сборка Docker-образа с GUI (устаревший, используйте rootless-версию)

### `start.sh`
Запуск приложения (Linux/Mac)

### `start-dev-windows.bat`
Запуск в режиме разработки на Windows (mock-режим)

---

## Проверка образа

После создания образа проверьте:

```bash
# Список образов
podman images

# Должен показать:
# REPOSITORY             TAG    IMAGE ID      CREATED        SIZE
# localhost/astra-linux  se     xxxxxxxxxxxx  X minutes ago  XXX MB

# Тестовый запуск
podman run --rm -it localhost/astra-linux:se /bin/bash
```

---

## Решение проблем

### Образ не виден после создания

См. **[../PODMAN_QUICK_FIX.md](../PODMAN_QUICK_FIX.md)**

### Ошибка "short-name did not resolve"

Используйте полное имя с префиксом:
```bash
podman run --rm -it localhost/astra-linux:se /bin/bash
```

### Ошибка "connection refused"

Образ не найден в локальном хранилище. Проверьте:
```bash
podman images
```

---

## Дополнительная информация

- [Быстрое решение проблем с Podman](../PODMAN_QUICK_FIX.md)
- [Подробная информация о проблемах с образами](../docs/PODMAN_IMAGE_FIX.md)
- [Общее решение проблем](../docs/TROUBLESHOOTING.md)
- [Установка на Astra Linux](../docs/ASTRA_LINUX.md)

