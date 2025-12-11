# Решение проблем

Этот документ содержит решения наиболее распространённых проблем при работе с Astra Linux Training Simulator.

## Содержание

1. [Проблемы с видимостью образов Podman](#проблемы-с-видимостью-образов-podman) ⚠️ **ВАЖНО**
2. [Проблемы с созданием образа](#проблемы-с-созданием-образа)
3. [Проблемы с проверкой уязвимостей](#проблемы-с-проверкой-уязвимостей)
4. [Проблемы с короткими именами образов Podman](#проблемы-с-короткими-именами-образов-podman)
5. [Проблемы с запуском контейнеров](#проблемы-с-запуском-контейнеров)

---

## Проблемы с видимостью образов Podman

### Проблема: Образ создан, но `podman images` показывает пустой список

**Симптомы**:
- Скрипт `create-astra-image.sh` завершается успешно
- В логах видно, что образ создан
- Команда `podman images` показывает пустой список
- При попытке запустить контейнер: `Error: short-name did not resolve`

**Причина**: Образ создан в root-контексте (через sudo), а проверяется в rootless-контексте (без sudo). Root и rootless podman используют разные хранилища:
- Root: `/var/lib/containers/storage/`
- Rootless: `~/.local/share/containers/storage/`

**Быстрое решение**:

См. **[PODMAN_QUICK_FIX.md](../PODMAN_QUICK_FIX.md)** для быстрого решения.

**Вариант 1: Перенос существующего образа**

```bash
cd scripts
./fix-podman-images.sh
```

**Вариант 2: Создание нового образа без sudo (рекомендуется)**

```bash
cd scripts
./create-astra-image-rootless.sh
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

**Диагностика**:

```bash
# Проверка у обычного пользователя
podman images

# Проверка у root
sudo podman images

# Если образ виден только у root - проблема подтверждена
```

**Подробная информация**: См. [docs/PODMAN_IMAGE_FIX.md](PODMAN_IMAGE_FIX.md)

---

## Проблемы с созданием образа

### Проблема: "Couldn't find these debs: perl-modules-5.28"

**Причина**: В Astra Linux 1.8 пакет `perl-modules-5.28` может отсутствовать в репозитории или иметь другое название.

**Решение**:

**Вариант 1: Использовать обновлённый скрипт (рекомендуется)**

Скрипт `create-astra-image.sh` автоматически определяет версию и использует правильные пакеты:

```bash
cd scripts
sudo ./create-astra-image.sh
```

**Вариант 2: Создать минимальный образ без опциональных пакетов**

```bash
sudo debootstrap \
    --no-check-gpg \
    --variant=minbase \
    --components=main,contrib,non-free \
    1.8_x86-64 \
    /var/docker-chroot \
    http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main

# Создание образа
sudo tar -C /var/docker-chroot -cpf - . | \
podman import - localhost/astra-linux:se \
    --change "ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    --change 'CMD ["/bin/bash"]' \
    --change "ENV LANG=ru_RU.UTF-8"
```

**Вариант 3: Установить пакеты после создания образа**

```bash
# Создать минимальный образ
sudo debootstrap --variant=minbase 1.8_x86-64 /var/docker-chroot \
    http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main

# Создать образ
sudo tar -C /var/docker-chroot -cpf - . | \
podman import - localhost/astra-linux:se

# Установить пакеты в контейнере
podman run -it localhost/astra-linux:se bash
apt update
apt install -y locales nano gawk lsb-release acl
exit

# Сохранить изменения
podman commit <container_id> localhost/astra-linux:se
```

### Проблема: "Репозиторий не содержит файла Release"

**Причина**: Репозиторий недоступен или использует другой формат.

**Решение**:

1. **Проверьте доступность репозитория:**
   ```bash
   curl -I http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main/
   ```

2. **Используйте другой репозиторий:**
   ```bash
   # Для Astra Linux 1.8
   REPO="http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main"
   
   # Или локальный репозиторий
   REPO="file:///srv/repo/1.8_x86-64"
   ```

3. **Используйте репозиторий с обновлениями:**
   ```bash
   REPO="http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-update"
   ```

### Альтернативные способы создания образа

**Способ 1: Загрузка из реестра Astra Linux (рекомендуется)**

```bash
# Автоматически (через скрипт)
./scripts/pull-astra-image.sh

# Или вручную
podman pull registry.astralinux.ru/library/astra/ubi18:1.8.1
podman tag registry.astralinux.ru/library/astra/ubi18:1.8.1 localhost/astra-linux:se
```

**Способ 2: Использовать готовый образ из файла**

```bash
./scripts/import-astra-image.sh /path/to/astra-image.tar
```

**Способ 3: Экспорт из работающей системы**

```bash
# На работающей системе Astra Linux
sudo tar -C / -cpf - \
    --exclude=/proc --exclude=/sys --exclude=/dev \
    --exclude=/tmp --exclude=/var/tmp \
    . | podman import - localhost/astra-linux:se
```

---

## Проблемы с проверкой уязвимостей

### Проблема: "vulnerability detected"

**Причина**: Встроенная проверка уязвимостей в пакетах блокирует установку пакетов с известными уязвимостями.

**Решение**:

**Способ 1: Отключение проверки уязвимостей (для создания образа)**

Скрипт `create-astra-image.sh` автоматически отключает проверку. Если создаёте вручную:

```bash
# В chroot окружении создайте конфигурацию
sudo mkdir -p /var/docker-chroot/etc/apt/apt.conf.d/
echo 'APT::Get::AllowUnauthenticated "true";' | sudo tee /var/docker-chroot/etc/apt/apt.conf.d/99no-vuln-check
echo 'Acquire::AllowInsecureRepositories "true";' | sudo tee -a /var/docker-chroot/etc/apt/apt.conf.d/99no-vuln-check

# Затем обновляйте пакеты с флагами
sudo chroot /var/docker-chroot bash -c "
    apt update -o APT::Get::AllowUnauthenticated=true
    apt dist-upgrade -y --allow-unauthenticated
"
```

**Способ 2: Использование обновлённого репозитория**

```bash
REPO="http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main"
CODENAME="1.8_x86-64"

sudo debootstrap \
    --no-check-gpg \
    --components=main,contrib,non-free \
    "$CODENAME" \
    /var/docker-chroot \
    "$REPO"
```

**Способ 3: Использование минимального образа без обновлений**

```bash
sudo debootstrap \
    --variant=minbase \
    --no-check-gpg \
    --components=main,contrib,non-free \
    1.8_x86-64 \
    /var/docker-chroot \
    http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main

# Создание образа БЕЗ обновлений
sudo tar -C /var/docker-chroot -cpf - . | \
podman import - localhost/astra-linux:se \
    --change "ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    --change 'CMD ["/bin/bash"]' \
    --change "ENV LANG=ru_RU.UTF-8"
```

⚠️ **Внимание**: Отключение проверки уязвимостей используется только для создания образа тренажёра. В продакшене всегда используйте обновлённые пакеты.

---

## Проблемы с короткими именами образов Podman

### Проблема: "short-name did not resolve"

**Ошибка**:
```
Error: short-name "astra-linux:se" did not resolve to an alias and no unqualified-search registries are defined in "/etc/containers/registries.conf"
```

**Причина**: Podman требует полное имя образа (с префиксом репозитория) или настройку unqualified-search registries для коротких имён.

**Решение 1: Использовать localhost/ префикс (рекомендуется)**

```bash
# Вместо:
podman run --rm -it astra-linux:se /bin/bash

# Используйте:
podman run --rm -it localhost/astra-linux:se /bin/bash
```

**Решение 2: Настроить unqualified-search registries**

Добавьте настройку в `~/.config/containers/registries.conf`:

```bash
mkdir -p ~/.config/containers
cat > ~/.config/containers/registries.conf << 'EOF'
[registries.search]
registries = ['docker.io', 'quay.io', 'registry.astralinux.ru']
EOF
```

**Решение 3: Использовать ID образа**

```bash
# Список образов с ID
podman images

# Запуск по ID
podman run --rm -it <IMAGE_ID> /bin/bash
```

**Примечание**: Скрипты проекта автоматически используют `localhost/` префикс для локальных образов.

---

## Проблемы с запуском контейнеров

### Проблема: Образ создаётся, но контейнер не запускается

**Решение**:

1. **Проверьте образ:**
   ```bash
   podman images | grep astra-linux
   ```

2. **Проверьте запуск:**
   ```bash
   podman run --rm -it localhost/astra-linux:se /bin/bash
   ```

3. **Если ошибка с правами (rootless режим):**
   ```bash
   podman run --rm -it --userns=keep-id localhost/astra-linux:se /bin/bash
   ```

4. **Проверьте версию образа:**
   ```bash
   podman run --rm localhost/astra-linux:se cat /etc/os-release
   ```

### Проблема: Ошибка с user_namespaces

**Причина**: В hardened ядре Astra Linux отключены user_namespaces (CONFIG_USER_NS), необходимые для rootless контейнеров.

**Решение**: Используйте привилегированный режим Podman или используйте обычное (не hardened) ядро.

---

## Проверка созданного образа

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

---

## Рекомендации

1. **Используйте минимальный образ** - он быстрее создаётся и занимает меньше места
2. **Устанавливайте пакеты по мере необходимости** - не все пакеты нужны сразу
3. **Используйте готовые образы** - если доступны официальные образы Astra Linux
4. **Всегда используйте `localhost/` префикс** для локальных образов

---

## Дополнительная информация

- [Podman Short Names](https://www.redhat.com/sysadmin/container-image-short-names)
- [Podman Registries Configuration](https://github.com/containers/image/blob/main/docs/containers-registries.conf.5.md)
- [Astra Linux Documentation](https://wiki.astralinux.ru/)

