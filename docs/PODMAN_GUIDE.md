# Руководство по работе с Podman в Astra Linux Training Simulator

Полное руководство по созданию образов, решению проблем и работе с Podman в проекте.

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Создание образов](#создание-образов)
3. [Проблема с видимостью образов](#проблема-с-видимостью-образов)
4. [Решение распространённых проблем](#решение-распространённых-проблем)
5. [Дополнительная информация](#дополнительная-информация)

---

## Быстрый старт

### Рекомендуемый способ (rootless, без sudo)

```bash
cd scripts
./create-astra-image.sh --vnc
```

Этот скрипт:
- ✅ Не требует sudo
- ✅ Загружает готовый образ из реестра Astra Linux
- ✅ Автоматически добавляет VNC если указан флаг `--vnc`
- ✅ Правильно работает с rootless podman

---

## Создание образов

### Базовый образ (без GUI)

```bash
cd scripts
./create-astra-image.sh
```

Создаёт образ `localhost/astra-linux:se` для CLI-миссий (уровни B и C).

### Образ с VNC (для GUI)

```bash
cd scripts
./create-astra-image.sh --vnc
```

Создаёт образ `localhost/astra-linux:vnc` с:
- TigerVNC Server
- noVNC (доступ через браузер)
- XFCE Desktop
- Автозапуск VNC

### Параметры скрипта

```bash
./create-astra-image.sh [OPTIONS]

Опции:
  --vnc              Создать образ с VNC поддержкой
  --no-vnc           Создать базовый образ без VNC (по умолчанию)
  --rootless         Использовать rootless режим (по умолчанию)
  --with-sudo        Использовать sudo для создания
  --help             Показать справку
```

### Альтернативные способы

**Через debootstrap (требует sudo)**:
```bash
sudo ./create-astra-image.sh --with-sudo
```

**Из готового tar-архива**:
```bash
./import-astra-image.sh /path/to/image.tar
```

---

## Проблема с видимостью образов

### Симптомы

- Скрипт завершается успешно
- `podman images` показывает пустой список
- Ошибка: `Error: short-name did not resolve`

### Причина

Образ создан в **root-контексте** (через sudo), а проверяется в **rootless-контексте** (без sudo).

Root и rootless podman используют разные хранилища:
- Root: `/var/lib/containers/storage/`
- Rootless: `~/.local/share/containers/storage/`

### Быстрое решение

**Вариант 1: Автоматический перенос**
```bash
cd scripts
./fix-podman-images.sh
```

**Вариант 2: Пересоздать образ без sudo**
```bash
cd scripts
./create-astra-image.sh --vnc
```

**Вариант 3: Ручной перенос**
```bash
# 1. Экспорт от root
sudo podman save -o /tmp/astra.tar localhost/astra-linux:se

# 2. Изменение владельца
sudo chown $(id -u):$(id -g) /tmp/astra.tar

# 3. Импорт для пользователя
podman load -i /tmp/astra.tar

# 4. Тегирование
IMAGE_ID=$(podman images --format '{{.ID}}' | head -1)
podman tag $IMAGE_ID localhost/astra-linux:se

# 5. Очистка
rm /tmp/astra.tar
```

### Диагностика

```bash
# Проверка у обычного пользователя
podman images

# Проверка у root
sudo podman images

# Если образ виден только у root - проблема подтверждена
```

---

## Решение распространённых проблем

### 1. "Couldn't find these debs: perl-modules-5.28"

**Причина**: Пакет отсутствует в Astra Linux 1.8.

**Решение**: Скрипт автоматически пропускает отсутствующие пакеты. Если проблема сохраняется:

```bash
# Используйте готовый образ из реестра
./create-astra-image.sh --vnc
```

### 2. "short-name did not resolve"

**Решение**: Используйте полное имя с префиксом:

```bash
# Вместо:
podman run astra-linux:se

# Используйте:
podman run localhost/astra-linux:se
```

Или настройте registries:

```bash
mkdir -p ~/.config/containers
cat > ~/.config/containers/registries.conf << 'EOF'
unqualified-search-registries = ["localhost", "docker.io"]
EOF
```

### 3. "connection refused" при запуске

**Причина**: Podman пытается найти образ в реестре вместо локального хранилища.

**Решение**:

```bash
# Проверьте наличие образа
podman images

# Используйте полное имя
podman run localhost/astra-linux:se

# Или используйте IMAGE ID
podman run <IMAGE_ID>
```

### 4. Репозиторий недоступен

**Решение**: Используйте альтернативный репозиторий или готовый образ:

```bash
# Готовый образ из реестра Astra Linux
podman pull registry.astralinux.ru/library/astra/ubi18@sha256:850a91072ae82fcd7c718e979d044bd8f4a218a1f7938c23d98d019e1b5e7bfa
podman tag registry.astralinux.ru/library/astra/ubi18@sha256:850a91072ae82fcd7c718e979d044bd8f4a218a1f7938c23d98d019e1b5e7bfa localhost/astra-linux:se
```

### 5. Проблемы с user_namespaces

**Причина**: В hardened ядре Astra Linux отключены user_namespaces.

**Решение**: Используйте обычное (не hardened) ядро или привилегированный режим.

---

## Дополнительная информация

### Структура хранилищ Podman

```
Root podman:
/var/lib/containers/storage/
├── overlay/          # Слои образов
├── overlay-images/   # Метаданные
└── overlay-layers/   # Данные

Rootless podman:
~/.local/share/containers/storage/
├── overlay/
├── overlay-images/
└── overlay-layers/
```

### Полезные команды

```bash
# Информация о системе
podman info

# Путь к хранилищу
podman info --format '{{.Store.GraphRoot}}'

# Список образов
podman images

# Список контейнеров
podman ps -a

# Очистка неиспользуемых образов
podman image prune -a

# Удаление всех образов
podman rmi -a

# Логи контейнера
podman logs <container_name>

# Выполнить команду в контейнере
podman exec <container_name> <command>
```

### Проверка созданного образа

```bash
# Список образов
podman images

# Тестовый запуск
podman run --rm -it localhost/astra-linux:se /bin/bash

# Проверка содержимого
podman run --rm localhost/astra-linux:se ls -la /

# Проверка версии
podman run --rm localhost/astra-linux:se cat /etc/os-release
```

### Рекомендации

1. **Всегда используйте rootless режим** - безопаснее и проще
2. **Используйте localhost/ префикс** для локальных образов
3. **Регулярно очищайте** неиспользуемые образы и контейнеры
4. **Используйте готовые образы** из реестра когда возможно

---

## Ссылки

- [Podman Documentation](https://docs.podman.io/)
- [Astra Linux Wiki](https://wiki.astralinux.ru/)
- [Container Registries Configuration](https://github.com/containers/image/blob/main/docs/containers-registries.conf.5.md)

