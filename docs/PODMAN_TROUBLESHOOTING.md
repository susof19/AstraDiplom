# Решение проблем с Podman и образами

## Проблема: образы созданы, но недоступны

### Симптомы

```bash
$ podman images
REPOSITORY  TAG  IMAGE ID  CREATED  SIZE
# Пустой вывод, хотя образы были созданы

$ podman run --rm -it localhost/astra-linux:se /bin/bash
Error: unable to copy from source docker://localhost/astra-linux:se: 
       pinging container registry localhost: Get "https://localhost/v2/": 
       dial tcp 127.0.0.1:443: connect: connection refused
```

### Причина

Образы были созданы от пользователя `root` (через `sudo`), но вы пытаетесь запустить их от обычного пользователя. В rootless режиме Podman у каждого пользователя своё хранилище образов.

## Решение

### Вариант 1: Автоматическое исправление (рекомендуется)

Запустите диагностический скрипт:

```bash
cd scripts
chmod +x fix-podman-images.sh
./fix-podman-images.sh
```

Скрипт:
1. Проверит образы у текущего пользователя и root
2. Предложит экспортировать образ от root к пользователю
3. Настроит конфигурацию registries
4. Проверит работоспособность

### Вариант 2: Ручное исправление

#### Шаг 1: Проверьте образы от root

```bash
# Образы от root
sudo podman images

# Образы от текущего пользователя
podman images
```

#### Шаг 2: Экспортируйте образ

```bash
# От root экспортируем образ
sudo podman save -o /tmp/astra-linux.tar localhost/astra-linux:se

# Меняем владельца
sudo chown $USER:$USER /tmp/astra-linux.tar

# Импортируем для текущего пользователя
podman load -i /tmp/astra-linux.tar

# Тегируем
IMAGE_ID=$(podman images --format "{{.ID}}" | head -1)
podman tag $IMAGE_ID localhost/astra-linux:se
podman tag $IMAGE_ID astra-linux:se

# Удаляем временный файл
rm /tmp/astra-linux.tar
```

#### Шаг 3: Проверка

```bash
podman images | grep astra-linux
podman run --rm -it localhost/astra-linux:se /bin/bash
```

### Вариант 3: Пересоздание образа в rootless режиме

Создайте образ от обычного пользователя (без sudo):

```bash
cd scripts
chmod +x create-astra-image-rootless.sh
./create-astra-image-rootless.sh
```

Скрипт предложит 3 варианта:
1. **Готовый образ из реестра Astra Linux** (быстро, рекомендуется)
2. **Минимальный образ на базе Debian** (средне, для разработки)
3. **Базовый Debian** (быстро, для тестов)

## Настройка registries для коротких имён

Чтобы использовать короткие имена (`astra-linux:se` вместо `localhost/astra-linux:se`):

```bash
mkdir -p ~/.config/containers
cat > ~/.config/containers/registries.conf << 'EOF'
unqualified-search-registries = ["docker.io", "localhost"]

[[registry]]
location = "localhost"
insecure = true
EOF
```

После этого можно использовать:

```bash
podman run --rm -it astra-linux:se /bin/bash
```

## Проверка работоспособности

### 1. Проверка образов

```bash
# Список всех образов
podman images

# Поиск конкретного образа
podman images | grep astra-linux

# Информация об образе
podman inspect localhost/astra-linux:se
```

### 2. Тестовый запуск

```bash
# Интерактивная оболочка
podman run --rm -it localhost/astra-linux:se /bin/bash

# Выполнение команды
podman run --rm localhost/astra-linux:se cat /etc/os-release

# С пробросом порта (для GUI)
podman run --rm -p 5900:5900 localhost/astra-linux:se /bin/bash
```

### 3. Проверка конфигурации

```bash
# Версия Podman
podman --version

# Информация о системе
podman info

# Хранилище образов
podman info | grep -A 5 "store:"
```

## Частые ошибки и решения

### Ошибка: "short-name did not resolve to an alias"

```
Error: short-name "astra-linux:se" did not resolve to an alias 
       and no unqualified-search registries are defined
```

**Решение:** Настройте registries (см. выше) или используйте полное имя:

```bash
podman run --rm -it localhost/astra-linux:se /bin/bash
```

### Ошибка: "parsing reference"

```
Error: parsing reference "/bin/bash": invalid reference format
```

**Причина:** Неправильный порядок аргументов.

**Решение:**

```bash
# Неправильно
podman run --rm -it $(podman images --format '{{.ID}}' | head -1) /bin/bash

# Правильно
IMAGE_ID=$(podman images --format '{{.ID}}' | head -1)
podman run --rm -it $IMAGE_ID /bin/bash
```

### Ошибка: "connection refused" при обращении к localhost

```
Error: pinging container registry localhost: Get "https://localhost/v2/": 
       dial tcp 127.0.0.1:443: connect: connection refused
```

**Причина:** Podman пытается найти образ в удалённом registry `localhost`, но образ локальный.

**Решение:**

1. Проверьте, что образ существует: `podman images`
2. Используйте правильное имя: `localhost/astra-linux:se`
3. Настройте registries для локальных образов

### Образы есть у root, но не видны пользователю

**Причина:** В rootless режиме у каждого пользователя своё хранилище.

**Решение:** Используйте скрипт `fix-podman-images.sh` или экспортируйте образ вручную (см. Вариант 2).

## Полезные команды

```bash
# Удалить все образы
podman rmi -a

# Удалить конкретный образ
podman rmi localhost/astra-linux:se

# Удалить неиспользуемые образы
podman image prune

# Очистить всё (образы, контейнеры, volumes)
podman system prune -a

# Информация о хранилище
podman system df

# Логи Podman
journalctl --user -u podman

# Перезапуск Podman (rootless)
systemctl --user restart podman
```

## Дополнительная информация

### Где хранятся образы

- **Root:** `/var/lib/containers/storage/`
- **Rootless:** `~/.local/share/containers/storage/`

### Конфигурационные файлы

- **Системные:** `/etc/containers/`
- **Пользовательские:** `~/.config/containers/`

### Логи

```bash
# Логи контейнера
podman logs <container_id>

# Системные логи Podman
journalctl --user -u podman -f
```

## Контакты и поддержка

Если проблема не решена:

1. Запустите диагностику: `./scripts/fix-podman-images.sh`
2. Проверьте логи: `journalctl --user -u podman`
3. Создайте issue с выводом команд:
   ```bash
   podman version
   podman info
   podman images
   ```

## См. также

- [SETUP.md](SETUP.md) - Полная инструкция по установке
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Общие проблемы и решения
- [Официальная документация Podman](https://docs.podman.io/)

