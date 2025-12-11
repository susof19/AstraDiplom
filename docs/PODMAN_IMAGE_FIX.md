# Исправление проблем с образами Podman

## Проблема

После выполнения скрипта `create-astra-image.sh` образ создаётся успешно (видно в логах), но при запуске `podman images` список пуст. Это происходит из-за того, что:

1. **Образ создан в root-контексте** - скрипт запускался через `sudo`, поэтому образ сохранён в хранилище root-пользователя
2. **Проверка выполняется в rootless-контексте** - команда `podman images` без sudo проверяет хранилище текущего пользователя
3. **Разные хранилища** - root и rootless podman используют разные директории для хранения образов:
   - Root: `/var/lib/containers/storage/`
   - Rootless: `~/.local/share/containers/storage/`

## Диагностика

### Проверка образов у root
```bash
sudo podman images
```

### Проверка образов у пользователя
```bash
podman images
```

Если образ виден только у root - проблема подтверждена.

## Решения

### Решение 1: Автоматический перенос образа (рекомендуется)

Используйте скрипт для переноса образа из root в rootless режим:

```bash
cd scripts
./fix-podman-images.sh
```

Скрипт выполнит:
1. Экспорт образа из root podman в tar-архив
2. Изменение владельца файла
3. Импорт образа в rootless podman текущего пользователя
4. Правильное тегирование

### Решение 2: Создание образа в rootless режиме (лучший вариант)

Используйте rootless-версию скрипта, которая загружает готовый образ из реестра:

```bash
cd scripts
./create-astra-image-rootless.sh
```

**Преимущества:**
- Не требует sudo
- Быстрее (не нужен debootstrap)
- Использует официальный образ из реестра Astra Linux
- Правильно работает с rootless podman

### Решение 3: Ручной перенос

Если автоматические скрипты не работают:

```bash
# 1. Экспорт образа от root
sudo podman save -o /tmp/astra-linux.tar localhost/astra-linux:se

# 2. Изменение владельца
sudo chown $(id -u):$(id -g) /tmp/astra-linux.tar

# 3. Импорт для пользователя
podman load -i /tmp/astra-linux.tar

# 4. Тегирование
IMAGE_ID=$(podman images --format '{{.ID}}' | head -1)
podman tag $IMAGE_ID localhost/astra-linux:se
podman tag $IMAGE_ID astra-linux:se

# 5. Очистка
rm /tmp/astra-linux.tar

# 6. Проверка
podman images
```

## Проверка работоспособности

После применения любого из решений проверьте:

```bash
# Список образов
podman images

# Должен показать:
# REPOSITORY             TAG    IMAGE ID      CREATED        SIZE
# localhost/astra-linux  se     xxxxxxxxxxxx  X minutes ago  XXX MB

# Тестовый запуск
podman run --rm -it localhost/astra-linux:se /bin/bash
```

## Почему не сработал fallback?

В логе видно, что скрипт `create-astra-image.sh` не перешёл к fallback-варианту (загрузка из реестра), потому что:

1. **debootstrap завершился успешно** - базовая система была создана (строки 209-589 в логе)
2. **Образ был импортирован** - podman import выполнился (строки 792-798)
3. **Проблема возникла позже** - при попытке использовать образ от обычного пользователя

Fallback активируется только если `debootstrap` полностью провалится, но в вашем случае он отработал корректно.

## Рекомендации для будущего

### Для разработки на Astra Linux

1. **Используйте rootless режим** - всегда создавайте образы без sudo:
   ```bash
   ./create-astra-image-rootless.sh
   ```

2. **Проверяйте правильное хранилище**:
   ```bash
   # Образы пользователя
   podman images
   
   # Образы root (только для проверки)
   sudo podman images
   ```

3. **Используйте localhost/ префикс** для локальных образов:
   ```bash
   podman run --rm -it localhost/astra-linux:se /bin/bash
   ```

### Настройка registries.conf (опционально)

Если хотите использовать короткие имена без `localhost/`:

```bash
# Отредактируйте ~/.config/containers/registries.conf
mkdir -p ~/.config/containers
cat >> ~/.config/containers/registries.conf << 'EOF'
unqualified-search-registries = ["localhost", "docker.io"]
EOF
```

После этого будет работать:
```bash
podman run --rm -it astra-linux:se /bin/bash
```

## Дополнительная информация

### Структура хранилищ Podman

```
Root podman:
/var/lib/containers/storage/
├── overlay/          # Слои образов
├── overlay-images/   # Метаданные образов
└── overlay-layers/   # Данные слоёв

Rootless podman:
~/.local/share/containers/storage/
├── overlay/
├── overlay-images/
└── overlay-layers/
```

### Полезные команды

```bash
# Информация о системе podman
podman info

# Путь к хранилищу
podman info --format '{{.Store.GraphRoot}}'

# Очистка неиспользуемых образов
podman image prune -a

# Удаление всех образов
podman rmi -a

# Список контейнеров
podman ps -a
```

## Решение проблем

### Ошибка: "connection refused" при запуске

Если видите ошибку:
```
Error: initializing source docker://localhost/astra-linux:se: 
pinging container registry localhost: Get "https://localhost/v2/": 
dial tcp 127.0.0.1:443: connect: connection refused
```

**Причина:** Podman пытается найти образ в реестре `localhost`, а не в локальном хранилище.

**Решение:**
```bash
# Проверьте, что образ существует локально
podman images

# Используйте полное имя с localhost/
podman run --rm -it localhost/astra-linux:se /bin/bash

# Или используйте IMAGE ID напрямую
podman run --rm -it <IMAGE_ID> /bin/bash
```

### Образ не найден после перезагрузки

Если образ пропал после перезагрузки системы:

1. Проверьте, не используете ли вы временное хранилище
2. Убедитесь, что образ создан в правильном хранилище пользователя
3. Пересоздайте образ через rootless-скрипт

## Контакты и поддержка

Если проблема не решена:

1. Проверьте логи: `journalctl -xe | grep podman`
2. Соберите информацию: `podman info > podman-info.txt`
3. Создайте issue с приложением логов

