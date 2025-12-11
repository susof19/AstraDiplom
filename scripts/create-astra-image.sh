#!/bin/bash
# Скрипт создания образа Astra Linux для тренажёра
# Основан на официальной документации Astra Linux Special Edition
# Автоматически обходит проверку уязвимостей для создания образа тренажёра

set -e

# Определение версии Astra Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "astra" ]] || [[ "$ID" == "astraorel" ]]; then
        # Пытаемся определить версию из VERSION_ID или VERSION
        if [[ "$VERSION_ID" =~ ^1\.8 ]]; then
            CODENAME="${CODENAME:-1.8_x86-64}"
            REPO="${REPO:-http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main}"
        elif [[ "$VERSION_ID" =~ ^1\.7 ]]; then
            CODENAME="${CODENAME:-1.7_x86-64}"
            REPO="${REPO:-http://dl.astralinux.ru/astra/stable/1.7_x86-64/repository-main}"
        fi
    fi
fi

CODENAME="${CODENAME:-1.8_x86-64}"
REPO="${REPO:-http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main}"
IMAGE_NAME="${IMAGE_NAME:-astra-linux:se}"
CHROOT_DIR="${CHROOT_DIR:-/var/docker-chroot}"

# Fallback образ из реестра Astra Linux
FALLBACK_IMAGE="${FALLBACK_IMAGE:-registry.astralinux.ru/library/astra/ubi18:1.8.1}"

echo "🔨 Создание образа Astra Linux для тренажёра"
echo "Кодовое имя: $CODENAME"
echo "Репозиторий: $REPO"
echo "Имя образа: $IMAGE_NAME"
echo ""
echo "⚠️  Примечание: Для создания образа тренажёра проверка уязвимостей будет отключена"
echo "   Это безопасно, так как образ используется только в изолированных песочницах"
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

# Определение списка пакетов в зависимости от версии
# В Astra Linux 1.8 может не быть perl-modules-5.28
BASE_PACKAGES="ncurses-term,locales,nano,gawk,lsb-release,acl"

# Проверяем версию и добавляем соответствующие пакеты
if [[ "$CODENAME" =~ ^1\.8 ]]; then
    # Для Astra Linux 1.8 используем минимальный набор (perl-modules может отсутствовать)
    PACKAGES="$BASE_PACKAGES"
    echo "Используется минимальный список пакетов для Astra Linux 1.8"
else
    # Для более старых версий пробуем добавить perl-modules
    PACKAGES="$BASE_PACKAGES,perl-modules-5.28"
    echo "Используется список пакетов для Astra Linux 1.7"
fi

# Создание chroot с отключением проверки уязвимостей
echo "Создание базового окружения (это может занять несколько минут)..."
echo "Пакеты: $PACKAGES"

# Пробуем создать с полным списком пакетов
DEBOOTSTRAP_SUCCESS=false
if debootstrap \
    --no-check-gpg \
    --variant=minbase \
    --include "$PACKAGES" \
    --components=main,contrib,non-free \
    "$CODENAME" \
    "$CHROOT_DIR" \
    "$REPO" 2>&1 | tee /tmp/debootstrap.log; then
    DEBOOTSTRAP_SUCCESS=true
else
    # Если не получилось, пробуем без проблемных пакетов
    if grep -q "Couldn't find these debs" /tmp/debootstrap.log; then
        echo ""
        echo "⚠️  Некоторые пакеты не найдены, создаём минимальный образ..."
        echo "Пробуем без опциональных пакетов..."
        
        # Создаём минимальный образ только с базовыми пакетами
        if debootstrap \
            --no-check-gpg \
            --variant=minbase \
            --components=main,contrib,non-free \
            "$CODENAME" \
            "$CHROOT_DIR" \
            "$REPO" 2>&1 | tee -a /tmp/debootstrap.log; then
            DEBOOTSTRAP_SUCCESS=true
            
            # Устанавливаем пакеты после создания chroot (опционально)
            echo "Установка дополнительных пакетов в chroot (если доступны)..."
            chroot "$CHROOT_DIR" bash -c "
                export DEBIAN_FRONTEND=noninteractive
                apt update -o APT::Get::AllowUnauthenticated=true 2>/dev/null || apt update 2>/dev/null || true
                
                # Устанавливаем только те пакеты, которые доступны
                for pkg in ncurses-term locales nano gawk lsb-release acl mc; do
                    apt install -y --allow-unauthenticated \$pkg 2>/dev/null || \
                    apt install -y \$pkg 2>/dev/null || echo \"Пакет \$pkg недоступен, пропускаем\"
                done || true
            " || echo "⚠️  Некоторые пакеты не установлены, продолжаем..."
        fi
    fi
fi

rm -f /tmp/debootstrap.log

# Если debootstrap не удался, используем fallback - готовый образ из реестра
if [ "$DEBOOTSTRAP_SUCCESS" = false ]; then
    echo ""
    echo "❌ Не удалось создать образ через debootstrap"
    echo "🔄 Используем fallback: готовый образ из реестра Astra Linux"
    echo ""
    
    echo "📥 Загрузка образа из реестра: $FALLBACK_IMAGE"
    if podman pull "$FALLBACK_IMAGE"; then
        echo "✅ Образ загружен из реестра"
        
        # Тегируем образ с нужным именем (используем localhost/ для локальных образов)
        podman tag "$FALLBACK_IMAGE" "localhost/$IMAGE_NAME"
        podman tag "$FALLBACK_IMAGE" "$IMAGE_NAME" 2>/dev/null || true
        echo "✅ Образ помечен как localhost/$IMAGE_NAME и $IMAGE_NAME"
        
        echo ""
        echo "✅ Образ создан из реестра: localhost/$IMAGE_NAME"
        echo ""
        echo "Проверка образа:"
        podman images | grep -E "REPOSITORY|$IMAGE_NAME|localhost/$IMAGE_NAME" || podman images
        
        echo ""
        echo "💡 Тестовый запуск:"
        echo "   podman run --rm -it localhost/$IMAGE_NAME /bin/bash"
        
        exit 0
    else
        echo "❌ Не удалось загрузить образ из реестра"
        echo "💡 Проверьте доступность реестра: $FALLBACK_IMAGE"
        echo "💡 Или попробуйте создать образ вручную"
        exit 1
    fi
fi

# Настройка окружения
echo ""
echo "⚙️  Настройка окружения..."
cp /etc/resolv.conf "$CHROOT_DIR/etc/resolv.conf"
if [ -f /etc/apt/sources.list ]; then
    cp /etc/apt/sources.list "$CHROOT_DIR/etc/apt/sources.list"
fi

# Отключение проверки уязвимостей в chroot (для создания образа)
echo ""
echo "🔧 Отключение проверки уязвимостей в chroot..."
# Создаём конфигурацию для отключения проверки уязвимостей
cat > "$CHROOT_DIR/etc/apt/apt.conf.d/99no-vuln-check" << 'EOF'
APT::Get::AllowUnauthenticated "true";
Acquire::AllowInsecureRepositories "true";
EOF

# Обновление и настройка локали
echo ""
echo "🌐 Настройка локали..."
chroot "$CHROOT_DIR" bash -c "
    export DEBIAN_FRONTEND=noninteractive
    apt update -o Acquire::AllowInsecureRepositories=true -o APT::Get::AllowUnauthenticated=true 2>/dev/null || \
    apt update 2>/dev/null || true
    
    # Пробуем обновить, но не критично если не получится
    apt dist-upgrade -y -o APT::Get::AllowUnauthenticated=true --allow-unauthenticated 2>/dev/null || \
    apt dist-upgrade -y --allow-unauthenticated 2>/dev/null || \
    echo 'Обновление пропущено' || true
    
    # Настройка локали
    echo 'ru_RU.UTF-8 UTF-8' >> /etc/locale.gen 2>/dev/null || true
    echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen 2>/dev/null || true
    locale-gen 2>/dev/null || true
    update-locale ru_RU.UTF-8 2>/dev/null || true
" || {
    echo "⚠️  Некоторые операции настройки пропущены"
    echo "💡 Продолжаем создание образа..."
}

# Создание образа
echo ""
echo "📦 Создание образа Podman..."
TEMP_IMAGE_ID=$(tar -C "$CHROOT_DIR" -cpf - . | \
podman import - \
    --change "ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    --change 'CMD ["/bin/bash"]' \
    --change "ENV LANG=ru_RU.UTF-8" 2>/dev/null | grep -oP 'sha256:[a-f0-9]+' || echo "")

if [ -z "$TEMP_IMAGE_ID" ]; then
    # Если не получили ID из вывода, пробуем другой способ
    echo "Импорт образа..."
    tar -C "$CHROOT_DIR" -cpf - . | podman import - > /tmp/podman-import.log 2>&1
    TEMP_IMAGE_ID=$(grep -oP 'sha256:[a-f0-9]+' /tmp/podman-import.log | head -1)
fi

if [ -z "$TEMP_IMAGE_ID" ]; then
    echo "❌ Не удалось получить ID созданного образа"
    echo "Попробуйте использовать: podman images"
    exit 1
fi

# Тегируем образ с правильным именем (localhost/ для локальных образов)
echo "Тегирование образа как localhost/$IMAGE_NAME..."
podman tag "$TEMP_IMAGE_ID" "localhost/$IMAGE_NAME" || podman tag "$TEMP_IMAGE_ID" "$IMAGE_NAME"

# Также создаём тег без localhost/ для совместимости
podman tag "$TEMP_IMAGE_ID" "$IMAGE_NAME" 2>/dev/null || true

echo ""
echo "✅ Образ создан: $IMAGE_NAME"
echo ""

# Показываем все образы для отладки
echo "📋 Все доступные образы:"
podman images

echo ""
echo "🔍 Поиск образа $IMAGE_NAME:"
podman images | grep -E "REPOSITORY|$IMAGE_NAME|localhost/$IMAGE_NAME" || {
    echo "⚠️  Образ не найден по имени $IMAGE_NAME"
    echo "💡 Попробуйте использовать:"
    echo "   podman images"
    echo "   podman run --rm -it <IMAGE_ID> /bin/bash"
}

echo ""
echo "📝 Информация об образе:"
# Пробуем разные варианты имени
for img_name in "localhost/$IMAGE_NAME" "$IMAGE_NAME"; do
    if podman inspect "$img_name" --format='{{.RepoTags}} {{.RepoDigests}}' 2>/dev/null; then
        echo "✅ Образ найден: $img_name"
        break
    fi
done || echo "⚠️  Не удалось получить информацию об образе"

echo ""
echo "💡 Тестовый запуск:"
echo "   # Вариант 1 (с localhost/):"
echo "   podman run --rm -it localhost/$IMAGE_NAME /bin/bash"
echo ""
echo "   # Вариант 2 (по ID):"
echo "   podman run --rm -it \$(podman images --format '{{.ID}}' | head -1) /bin/bash"
echo ""
echo "   # Вариант 3 (если настроены unqualified-search registries):"
echo "   podman run --rm -it $IMAGE_NAME /bin/bash"

