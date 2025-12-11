# Быстрое решение проблемы с образами Podman

## Проблема
После запуска `create-astra-image.sh` образ создаётся, но `podman images` показывает пустой список.

## Причина
Образ создан в root-контексте (через sudo), а проверяется в rootless-контексте (без sudo). Это разные хранилища.

## Быстрое решение

### Вариант 1: Перенос существующего образа (если уже создан через sudo)

```bash
cd scripts
./fix-podman-images.sh
```

### Вариант 2: Создание нового образа без sudo (рекомендуется)

```bash
cd scripts
./create-astra-image-rootless.sh
```

Этот скрипт:
- ✅ Не требует sudo
- ✅ Загружает готовый образ из реестра Astra Linux
- ✅ Быстрее работает
- ✅ Правильно работает с rootless podman

## Проверка

```bash
# Проверить список образов
podman images

# Должен показать:
# REPOSITORY             TAG    IMAGE ID      CREATED        SIZE
# localhost/astra-linux  se     xxxxxxxxxxxx  X minutes ago  XXX MB

# Тестовый запуск
podman run --rm -it localhost/astra-linux:se /bin/bash
```

## Если ничего не помогло

### 1. Проверьте, где находится образ

```bash
# У обычного пользователя
podman images

# У root (для диагностики)
sudo podman images
```

### 2. Ручной перенос

```bash
# Экспорт от root
sudo podman save -o /tmp/astra.tar localhost/astra-linux:se

# Изменение владельца
sudo chown $(id -u):$(id -g) /tmp/astra.tar

# Импорт для пользователя
podman load -i /tmp/astra.tar

# Тегирование
IMAGE_ID=$(podman images --format '{{.ID}}' | head -1)
podman tag $IMAGE_ID localhost/astra-linux:se

# Очистка
rm /tmp/astra.tar
```

### 3. Альтернативный образ для тестирования

Если реестр Astra Linux недоступен, используйте Debian для тестирования:

```bash
podman pull debian:12
podman tag debian:12 localhost/astra-linux:se
```

## Подробная документация

Смотрите `docs/PODMAN_IMAGE_FIX.md` для полной информации.

## Для разработки на Windows

Если вы разрабатываете на Windows, используйте mock-режим:

1. Отредактируйте `backend/.env`:
   ```
   MOCK_SANDBOX=true
   ```

2. Запустите backend:
   ```bash
   cd backend
   python run.py
   ```

Mock-режим эмулирует работу контейнеров без реального Podman.

