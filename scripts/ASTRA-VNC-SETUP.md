# Настройка образа Astra Linux с VNC

Этот документ описывает, как настроить и использовать готовый образ Astra Linux с VNC из репозитория [shinbatsu/astra-ui-vnc-container](https://github.com/shinbatsu/astra-ui-vnc-container).

## Быстрый старт

### ⚠️ Важное замечание

Репозиторий [shinbatsu/astra-ui-vnc-container](https://github.com/shinbatsu/astra-ui-vnc-container) использует приватный базовый образ `astra-fly:v1.7.6`, который недоступен в публичном Docker Hub. Это может привести к ошибке `pull access denied`.

**Рекомендуется использовать собственный Dockerfile** (см. альтернативный вариант ниже).

### Вариант 1: Автоматическая настройка (может не работать из-за приватного образа)

Запустите скрипт настройки:

```bash
./scripts/setup-astra-vnc-image.sh
```

Скрипт автоматически:
1. Клонирует репозиторий с образом
2. Попытается собрать базовый образ `astra-fly:v1.7.6` (если Dockerfile.fly существует)
3. Соберет Docker/Podman образ `localhost/astra-vnc:latest`
4. Подготовит образ к использованию

**Если сборка не удалась**, используйте альтернативный вариант ниже.

### Вариант 2: Использовать собственный Dockerfile (рекомендуется)

Если сборка из репозитория не удалась, используйте наш собственный Dockerfile:

```bash
./scripts/create-astra-image.sh --vnc
# Выберите вариант 5: Astra Linux (из реестра, если доступен)
```

Это создаст образ `localhost/linux-gui-vnc:astra` с использованием официального реестра Astra Linux.

### Вариант 3: Через create-astra-image.sh (попытка использовать репозиторий)

При создании образа выберите опцию 6:

```bash
./scripts/create-astra-image.sh
# Выберите вариант 6: Astra Linux с VNC (из репозитория shinbatsu/astra-ui-vnc-container)
```

**Примечание**: Этот вариант может не работать из-за приватного базового образа.

## Использование

После настройки образ будет автоматически использоваться при выборе дистрибутива `astra` в настройках песочницы.

### В конфигурации

Образ настроен в `backend/config.py`:

```python
DISTRO_GUI_IMAGES = {
    "debian": "localhost/linux-gui-vnc:debian",
    "ubuntu": "localhost/linux-gui-vnc:ubuntu",
    "astra": "localhost/astra-vnc:latest"  # Используется образ из репозитория
}
```

### Особенности образа

- **Порт noVNC**: Образ использует порт `80` для noVNC внутри контейнера (вместо стандартного `6080`)
- **Путь noVNC**: noVNC доступен по корневому пути `/` (вместо `/vnc.html`)
- **Window Manager**: Использует Fly window manager (легковесный оконный менеджер)
- **VNC**: Встроенный VNC сервер с noVNC клиентом

### Автоматическая адаптация

Код автоматически определяет, что используется образ `astra-vnc`, и:
- Пробрасывает порт `80` вместо `6080` для noVNC
- Использует корневой путь `/` для noVNC URL
- Настраивает все параметры автоматически

## Проверка образа

Проверьте, что образ создан:

```bash
# Для Podman
podman images | grep astra-vnc

# Для Docker
docker images | grep astra-vnc
```

Должен отображаться образ `localhost/astra-vnc:latest` или `astra-vnc:latest`.

## Ручная сборка (опционально)

Если нужно собрать образ вручную:

```bash
# Клонируем репозиторий
git clone https://github.com/shinbatsu/astra-ui-vnc-container.git temp-astra-vnc
cd temp-astra-vnc

# Собираем образ
docker build -f Dockerfile.vnc -t localhost/astra-vnc:latest .
# или
podman build -f Dockerfile.vnc -t localhost/astra-vnc:latest .

# Очищаем
cd ..
rm -rf temp-astra-vnc
```

## Устранение неполадок

### Образ не собирается: "pull access denied" для astra-fly:v1.7.6

**Проблема**: Базовый образ `astra-fly:v1.7.6` недоступен в Docker Hub, так как это приватный репозиторий.

**Решения**:

1. **Использовать собственный Dockerfile (рекомендуется)**:
   ```bash
   ./scripts/create-astra-image.sh --vnc
   # Выберите вариант 5: Astra Linux (из реестра, если доступен)
   ```

2. **Связаться с автором репозитория**:
   - Репозиторий: https://github.com/shinbatsu/astra-ui-vnc-container
   - Попросить сделать базовый образ `astra-fly:v1.7.6` публичным
   - Или предоставить доступ к приватному репозиторию

3. **Проверить логи**:
   ```bash
   docker build -f temp-astra-vnc/Dockerfile.vnc -t localhost/astra-vnc:latest temp-astra-vnc/
   ```

### Образ не собирается (другие причины)

1. Проверьте подключение к интернету
2. Убедитесь, что Git установлен: `sudo apt-get install git`
3. Проверьте доступ к Docker/Podman: `docker info` или `podman info`
4. Убедитесь, что Dockerfile.fly существует в репозитории

### Образ не используется

1. Проверьте, что образ существует: `docker images | grep astra-vnc`
2. Убедитесь, что в `backend/config.py` указан правильный образ для `astra`
3. Перезапустите backend после изменения конфигурации

### Проблемы с портами

Образ использует порт `80` для noVNC внутри контейнера. Код автоматически адаптирует это, но если возникают проблемы:

1. Проверьте, что порты проброшены правильно: `docker ps` или `podman ps`
2. Убедитесь, что порты не заняты другими процессами

## Дополнительная информация

- [Репозиторий образа](https://github.com/shinbatsu/astra-ui-vnc-container)
- [Документация проекта](../README.md)
- [Настройка дистрибутивов](../DISTRO-SETUP.md)

