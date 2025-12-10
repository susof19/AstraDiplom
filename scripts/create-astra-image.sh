#!/bin/bash
# Скрипт создания образа Astra Linux для тренажёра
# Основан на официальной документации Astra Linux Special Edition

set -e

CODENAME="${CODENAME:-1.7_x86-64}"
REPO="${REPO:-http://dl.astralinux.ru/astra/stable/1.7_x86-64/repository-main}"
IMAGE_NAME="${IMAGE_NAME:-astra-linux:se}"
CHROOT_DIR="${CHROOT_DIR:-/var/docker-chroot}"

echo "🔨 Создание образа Astra Linux для тренажёра"
echo "Кодовое имя: $CODENAME"
echo "Репозиторий: $REPO"
echo "Имя образа: $IMAGE_NAME"
echo ""

# Проверка прав
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Скрипт должен запускаться с правами root (sudo)"
    exit 1
fi

# Проверка установленных пакетов
echo "Проверка зависимостей..."
for pkg in debootstrap podman; do
    if ! dpkg -l $pkg >/dev/null 2>/dev/null; then
        echo "Установка $pkg..."
        apt install -y $pkg
    fi
done

# Создание chroot-окружения
echo ""
echo "📦 Создание chroot-окружения в $CHROOT_DIR..."
if [ -d "$CHROOT_DIR" ]; then
    echo "⚠️  Каталог $CHROOT_DIR уже существует. Удалить? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        rm -rf "$CHROOT_DIR"
    else
        echo "Используется существующий каталог"
    fi
fi

debootstrap \
    --include ncurses-term,mc,locales,nano,gawk,lsb-release,acl,perl-modules-5.28 \
    --components=main,contrib,non-free \
    "$CODENAME" \
    "$CHROOT_DIR" \
    "$REPO"

# Настройка окружения
echo ""
echo "⚙️  Настройка окружения..."
cp /etc/resolv.conf "$CHROOT_DIR/etc/resolv.conf"
if [ -f /etc/apt/sources.list ]; then
    cp /etc/apt/sources.list "$CHROOT_DIR/etc/apt/sources.list"
fi

# Обновление и настройка локали
echo ""
echo "🌐 Настройка локали..."
chroot "$CHROOT_DIR" bash -c "
    apt update
    apt dist-upgrade -y
    echo 'ru_RU.UTF-8 UTF-8' >> /etc/locale.gen
    echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen
    locale-gen
    update-locale ru_RU.UTF-8
"

# Создание образа
echo ""
echo "📦 Создание образа Podman..."
tar -C "$CHROOT_DIR" -cpf - . | \
podman import - "$IMAGE_NAME" \
    --change "ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    --change 'CMD ["/bin/bash"]' \
    --change "ENV LANG=ru_RU.UTF-8"

echo ""
echo "✅ Образ создан: $IMAGE_NAME"
echo ""
echo "Проверка образа:"
podman images | grep -E "REPOSITORY|$IMAGE_NAME" || podman images

echo ""
echo "Тестовый запуск:"
echo "podman run --rm -it $IMAGE_NAME /bin/bash"

