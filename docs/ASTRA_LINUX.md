# Настройка для Astra Linux Special Edition

Этот документ содержит инструкции по установке и настройке проекта на Astra Linux Special Edition.

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Установка Podman](#установка-podman)
3. [Создание образа Astra Linux](#создание-образа-astra-linux)
4. [Настройка rootless режима](#настройка-rootless-режима)
5. [Особенности Astra Linux](#особенности-astra-linux)

---

## Быстрый старт

Самый простой способ - использовать скрипт быстрого старта:

```bash
cd AstraDiplom
chmod +x scripts/quickstart-astra.sh
./scripts/quickstart-astra.sh
```

Скрипт автоматически:
1. ✅ Установит все необходимые пакеты (Python, Node.js, Podman)
2. ✅ Настроит виртуальное окружение для backend
3. ✅ Установит зависимости frontend
4. ✅ Создаст скрипт запуска `start-trainer.sh`
5. ✅ Создаст ярлык на рабочем столе
6. ✅ Опционально создаст образ Astra Linux

### Запуск после установки

**Способ 1: Через скрипт**
```bash
./start-trainer.sh
```

**Способ 2: Через ярлык на рабочем столе**
Дважды кликните на "Astra Linux Trainer" на рабочем столе

**Способ 3: Вручную**

**Терминал 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python run.py
```

**Терминал 2 - Frontend:**
```bash
cd frontend/web
npm start
```

Откройте http://localhost:3000 в браузере.

---

## Установка Podman

### Вариант 1: Использование Podman напрямую

Podman может быть установлен из репозиториев Astra Linux:

```bash
# Установка Podman
sudo apt install podman

# Настройка rootless режима
podman system migrate
```

### Вариант 2: Использование Docker с rootless-helper-astra

Согласно официальной документации Astra Linux, можно использовать Docker в rootless режиме через `rootless-helper-astra`:

```bash
# Установка rootless-helper-astra
sudo apt install rootless-helper-astra

# Включение пользовательских служб Docker для rootless режима
# Замените <имя_пользователя> и <метка_безопасности> на реальные значения
sudo systemctl start rootless-docker@<имя_пользователя>@<метка_безопасности>

# Разрешить автоматический запуск
sudo systemctl enable rootless-docker@<имя_пользователя>@<метка_безопасности>
```

**Примечание**: В этом случае в конфигурации нужно использовать:
```python
PODMAN_BINARY = "rootlessenv podman"  # или "rootlessenv docker"
```

---

## Создание образа Astra Linux

### Способ 1: Использование скрипта (рекомендуется)

Используйте автоматический скрипт:

```bash
cd scripts
sudo ./create-astra-image.sh
```

Скрипт автоматически:
- Определяет версию Astra Linux
- Создаёт chroot-окружение через debootstrap
- Отключает проверку уязвимостей (для создания образа тренажёра)
- Создаёт образ Podman с правильным тегом (`localhost/astra-linux:se`)
- Использует fallback (загрузку из реестра), если создание не удаётся

### Способ 2: Использование debootstrap вручную

```bash
# Установка необходимых пакетов
sudo apt install debootstrap podman

# Создание chroot-окружения
sudo debootstrap \
    --include ncurses-term,locales,nano,gawk,lsb-release,acl \
    --components=main,contrib,non-free \
    1.8_x86-64 \
    /var/docker-chroot \
    http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main

# Отключение проверки уязвимостей (для создания образа тренажёра)
sudo mkdir -p /var/docker-chroot/etc/apt/apt.conf.d/
echo 'APT::Get::AllowUnauthenticated "true";' | sudo tee /var/docker-chroot/etc/apt/apt.conf.d/99no-vuln-check
echo 'Acquire::AllowInsecureRepositories "true";' | sudo tee -a /var/docker-chroot/etc/apt/apt.conf.d/99no-vuln-check

# Обновление и настройка локали
sudo chroot /var/docker-chroot bash -c "
    export DEBIAN_FRONTEND=noninteractive
    apt update -o APT::Get::AllowUnauthenticated=true
    apt dist-upgrade -y --allow-unauthenticated || echo 'Обновление пропущено'
    echo 'ru_RU.UTF-8 UTF-8' >> /etc/locale.gen
    echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen
    locale-gen
    update-locale ru_RU.UTF-8
"

# Создание образа
sudo tar -C /var/docker-chroot -cpf - . | \
podman import - localhost/astra-linux:se \
    --change "ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    --change 'CMD ["/bin/bash"]' \
    --change "ENV LANG=ru_RU.UTF-8"
```

### Способ 3: Загрузка из реестра

Если создание образа не удаётся, используйте готовый образ из реестра:

```bash
# Автоматически
./scripts/pull-astra-image.sh

# Или вручную
podman pull registry.astralinux.ru/library/astra/ubi18:1.8.1
podman tag registry.astralinux.ru/library/astra/ubi18:1.8.1 localhost/astra-linux:se
```

---

## Настройка rootless режима

### Проверка поддержки user_namespaces

В hardened ядре Astra Linux отключены user_namespaces (CONFIG_USER_NS), необходимые для rootless контейнеров.

Проверьте поддержку:
```bash
# Проверка поддержки user_namespaces
grep CONFIG_USER_NS /boot/config-$(uname -r) || echo "Не найдено"

# Если выводит CONFIG_USER_NS=y, то rootless режим поддерживается
# Если выводит CONFIG_USER_NS=n или ничего, то rootless режим не поддерживается
```

### Настройка rootless Podman

Если user_namespaces поддерживается:

```bash
# Инициализация rootless Podman
podman system migrate

# Проверка
podman info
```

### Ограничение памяти для контейнеров

Для работы ограничения памяти в контейнерах Docker/Podman добавьте в `/etc/default/grub`:

```bash
GRUB_CMDLINE_LINUX_DEFAULT="... cgroup_enable=memory swapaccount=1"
```

Затем:
```bash
sudo update-grub
sudo reboot
```

---

## Особенности Astra Linux

### CD-ROM репозитории

Astra Linux может быть настроена на использование CD-ROM как источника пакетов. Это может мешать установке пакетов.

**Решение**: Скрипт `quickstart-astra.sh` автоматически отключает CD-ROM репозитории. Если нужно сделать вручную:

```bash
# Отключение CD-ROM репозиториев
echo 'Acquire::cdrom::AutoDetect "false";' | sudo tee /etc/apt/apt.conf.d/99no-cdrom
echo 'Acquire::cdrom::mount "/dev/null";' | sudo tee -a /etc/apt/apt.conf.d/99no-cdrom
```

### Проверка уязвимостей

Astra Linux имеет встроенную проверку уязвимостей в пакетах. При создании образа для тренажёра эта проверка может блокировать установку пакетов.

**Решение**: Скрипт `create-astra-image.sh` автоматически отключает проверку уязвимостей в chroot-окружении. См. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) для подробностей.

### Hardened ядро

В hardened ядре отключены некоторые функции, необходимые для rootless контейнеров. Если вы используете hardened ядро, используйте привилегированный режим Podman.

### МКЦ (Мандатное управление доступом)

При работе с МКЦ могут потребоваться дополнительные настройки меток безопасности. Обычно для тренажёра это не требуется, так как контейнеры изолированы.

---

## Troubleshooting

Если возникли проблемы, см. [TROUBLESHOOTING.md](TROUBLESHOOTING.md) для подробных решений.

Основные проблемы:
- [Проблемы с созданием образа](TROUBLESHOOTING.md#проблемы-с-созданием-образа)
- [Проблемы с проверкой уязвимостей](TROUBLESHOOTING.md#проблемы-с-проверкой-уязвимостей)
- [Проблемы с короткими именами образов](TROUBLESHOOTING.md#проблемы-с-короткими-именами-образов-podman)

---

## Дополнительная информация

- [Официальная документация Astra Linux](https://wiki.astralinux.ru/)
- [Установка Docker в Astra Linux](https://wiki.astralinux.ru/pages/viewpage.action?pageId=118227456)
- [QUICKSTART.md](../QUICKSTART.md) - быстрый старт для других систем

