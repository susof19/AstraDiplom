# Настройка для Astra Linux Special Edition

## Установка Podman в Astra Linux

### Вариант 1: Использование Podman напрямую

Podman может быть установлен из репозиториев Astra Linux или собран из исходников.

```bash
# Установка Podman (если доступен в репозиториях)
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

## Создание образа Astra Linux для тренажёра

### Способ 1: Использование debootstrap (рекомендуется)

Согласно документации Astra Linux, образ создаётся через debootstrap:

```bash
# Установка необходимых пакетов
sudo apt install debootstrap podman

# Создание chroot-окружения
sudo debootstrap \
    --include ncurses-term,mc,locales,nano,gawk,lsb-release,acl,perl-modules-5.28 \
    --components=main,contrib,non-free 1.7_x86-64 \
    /var/docker-chroot \
    http://dl.astralinux.ru/astra/stable/1.7_x86-64/repository-main

# Настройка окружения
sudo cp /etc/resolv.conf /var/docker-chroot/etc/resolv.conf
sudo cp /etc/apt/sources.list /var/docker-chroot/etc/apt/sources.list

# Обновление и настройка локали
sudo chroot /var/docker-chroot
apt update
apt dist-upgrade
echo "ru_RU.UTF-8 UTF-8" >> /etc/locale.gen
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
update-locale ru_RU.UTF-8
exit

# Создание образа
sudo tar -C /var/docker-chroot -cpf - . | \
podman import - astra-linux:se \
    --change "ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    --change 'CMD ["/bin/bash"]' \
    --change "ENV LANG=ru_RU.UTF-8"
```

### Способ 2: Использование Dockerfile

Для уровня A (GUI) используйте Dockerfile из `images/Dockerfile.astra-gui`:

```bash
cd images
podman build -f Dockerfile.astra-gui -t astra-linux:latest .
```

## Особенности Astra Linux

### Метки безопасности (МКЦ)

При работе с МКЦ (многоуровневая классификация целостности) учитывайте:

- Каталог `/var` имеет метку безопасности `3:63:-1:ccnr`, позволяющую создавать файловые объекты с любыми метками
- Для работы пользователей в rootless режиме администратор должен создать доступный каталог с необходимой меткой безопасности

### Hardened ядро

**Важно**: При использовании hardened ядра непривилегированные контейнеры невозможны, так как в hardened ядре запрещено использование `user_namespaces` (CONFIG_USER_NS).

### Ограничение памяти

Для ограничения памяти контейнеров добавьте в `/etc/default/grub`:

```bash
GRUB_CMDLINE_LINUX_DEFAULT="... cgroup_enable=memory swapaccount=1"
sudo update-grub
# Перезагрузить ОС
```

Затем используйте опцию `--memory` при запуске:

```bash
podman run -it --memory 100m astra-linux:se /bin/sh
```

### Изоляция Docker (пониженный уровень целостности)

В Astra Linux Special Edition 1.8+ можно запустить контейнеризацию на пониженном уровне целостности:

```bash
# Включить изоляцию
sudo astra-docker-isolation enable

# Выключить изоляцию
sudo astra-docker-isolation disable
```

## Настройка тренажёра для Astra Linux

### Конфигурация

В `backend/config.py` установите:

```python
# Для прямого использования Podman
PODMAN_BINARY = "podman"
PODMAN_ROOTLESS = True

# ИЛИ для использования через rootless-helper-astra
PODMAN_BINARY = "rootlessenv podman"  # или "rootlessenv docker"
PODMAN_ROOTLESS = True
```

### Проверка работы

```bash
# Проверить доступность Podman
podman info

# Проверить образы
podman images

# Запустить тестовый контейнер
podman run --rm -it astra-linux:se /bin/bash
```

## Troubleshooting

### Ошибка с user_namespaces

Если получаете ошибку о user_namespaces:
- Проверьте, не используется ли hardened ядро
- Убедитесь, что ядро скомпилировано с CONFIG_USER_NS=y

### Ошибка с метками безопасности

Если возникают проблемы с метками безопасности:
- Убедитесь, что каталог для chroot имеет правильную метку
- Используйте `/var` или создайте каталог с меткой `3:63:-1:ccnr`

### DNS не работает в контейнере

Docker в rootless режиме использует только первый DNS сервер из `/etc/resolv.conf`. Проверьте:

```bash
dig +short docker.io @<IP-адрес_первого_DNS_сервера>
```

## Дополнительные ресурсы

- [Официальная документация Astra Linux по Docker](https://wiki.astralinux.ru/)
- [Создание собственного образа Astra Linux для Docker](https://wiki.astralinux.ru/)

