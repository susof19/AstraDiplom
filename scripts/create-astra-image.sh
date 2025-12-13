#!/bin/bash
# Скрипт создания образа контейнера для Linux Training Simulator
# Поддерживает создание образов на базе установленной ОС или публичных образов
# Поддерживает создание базового образа и образа с VNC
# Работает с Podman и Docker

set -e

# Параметры по умолчанию
USE_VNC=false
SHOW_HELP=false
BASE_IMAGE=""
IMAGE_NAME="linux-sandbox"

# Определение контейнерной команды (Podman или Docker)
CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo "❌ Ошибка: Podman или Docker не найдены"
    echo "💡 Установите один из них:"
    echo "   sudo apt-get install podman uidmap slirp4netns fuse-overlayfs"
    echo "   или"
    echo "   sudo apt-get install docker.io"
    exit 1
fi

# Проверка доступа к Docker/Podman
echo "🔍 Проверка доступа к $CONTAINER_CMD..."
if ! $CONTAINER_CMD info &>/dev/null; then
    echo "❌ Ошибка: нет доступа к $CONTAINER_CMD"
    echo ""
    if [ "$CONTAINER_CMD" = "docker" ]; then
        echo "💡 Для WSL с Docker Desktop:"
        echo "   1. Убедитесь, что Docker Desktop запущен в Windows"
        echo "   2. В настройках Docker Desktop включите интеграцию с WSL"
        echo "   3. Перезапустите WSL: wsl --shutdown (в PowerShell), затем откройте снова"
        echo ""
        echo "💡 Для Linux:"
        echo "   sudo usermod -aG docker $USER"
        echo "   (затем выйдите и войдите снова)"
    else
        echo "💡 Для Podman:"
        echo "   podman system migrate"
        echo "   или выйдите и войдите снова"
    fi
    echo ""
    read -p "Попробовать с sudo? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        CONTAINER_CMD="sudo $CONTAINER_CMD"
        echo "⚠️  Используется sudo для $CONTAINER_CMD"
    else
        exit 1
    fi
else
    echo "✅ Доступ к $CONTAINER_CMD подтвержден"
fi
echo ""

# Определение установленной ОС
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_ID="$ID"
        OS_VERSION_ID="${VERSION_ID:-}"
        OS_NAME="$NAME"
    else
        OS_ID="unknown"
        OS_VERSION_ID=""
        OS_NAME="Unknown"
    fi
}

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --vnc)
            USE_VNC=true
            shift
            ;;
        --no-vnc)
            USE_VNC=false
            shift
            ;;
        --base)
            BASE_IMAGE="$2"
            shift 2
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo "❌ Неизвестный параметр: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Показать справку
if [ "$SHOW_HELP" = true ]; then
    cat << EOF
Использование: ./create-astra-image.sh [OPTIONS]

Создание образа контейнера для Linux Training Simulator
Поддерживает Debian-based дистрибутивы и Astra Linux

Опции:
  --vnc              Создать образ с VNC поддержкой (TigerVNC + noVNC + XFCE)
  --no-vnc           Создать базовый образ без VNC (по умолчанию)
  --base IMAGE       Использовать указанный базовый образ (например, debian:12)
  --help, -h         Показать эту справку

Примеры:
  # Создать базовый образ (для CLI-миссий)
  ./create-astra-image.sh

  # Создать образ с VNC (для GUI-миссий)
  ./create-astra-image.sh --vnc

  # Использовать конкретный базовый образ
  ./create-astra-image.sh --base ubuntu:22.04 --vnc

Результат (новая схема именования):
  Базовый образ:  localhost/linux-base:{distro} (debian/ubuntu/astra)
  Образ с VNC:    localhost/linux-gui-vnc:{distro} (debian/ubuntu/astra)
  
Также создаются legacy теги для обратной совместимости:
  localhost/linux-sandbox:base
  localhost/linux-sandbox:vnc

EOF
    exit 0
fi

# Определяем установленную ОС
detect_os
echo "📋 Обнаружена ОС: $OS_NAME ($OS_ID $OS_VERSION_ID)"
echo ""

# Переходим в корень проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Выбор базового образа
if [ -z "$BASE_IMAGE" ]; then
    echo "🔍 Выбор базового образа..."
    echo ""
    echo "Доступные варианты:"
    echo "  1) Использовать установленную ОС ($OS_NAME)"
    echo "  2) Debian 12 (рекомендуется для универсальности)"
    echo "  3) Ubuntu 22.04 LTS"
    echo "  4) Ubuntu 24.04 LTS"
    echo "  5) Astra Linux (из реестра, если доступен)"
    echo "  6) Astra Linux с VNC (из репозитория shinbatsu/astra-ui-vnc-container)"
    echo "  7) Указать свой образ"
    echo ""
    read -p "Выберите вариант (1-7): " -n 1 -r
    echo
    echo ""
    
    case $REPLY in
        1)
            # Использовать установленную ОС
            case $OS_ID in
                debian)
                    BASE_IMAGE="debian:${OS_VERSION_ID:-12}"
                    echo "📥 Используем Debian ${OS_VERSION_ID:-12}"
                    ;;
                ubuntu)
                    BASE_IMAGE="ubuntu:${OS_VERSION_ID:-22.04}"
                    echo "📥 Используем Ubuntu ${OS_VERSION_ID:-22.04}"
                    ;;
                astra)
                    # Пробуем загрузить из реестра Astra Linux
                    ASTRA_IMAGE="registry.astralinux.ru/library/astra/ubi18@sha256:850a91072ae82fcd7c718e979d044bd8f4a218a1f7938c23d98d019e1b5e7bfa"
                    if $CONTAINER_CMD pull "$ASTRA_IMAGE" 2>/dev/null; then
                        BASE_IMAGE="$ASTRA_IMAGE"
                        echo "📥 Используем Astra Linux из реестра"
                    else
                        echo "⚠️  Не удалось загрузить Astra Linux, используем Debian 12"
                        BASE_IMAGE="debian:12"
                    fi
                    ;;
                *)
                    echo "⚠️  ОС $OS_ID не поддерживается напрямую, используем Debian 12"
                    BASE_IMAGE="debian:12"
                    ;;
            esac
            ;;
        2)
            BASE_IMAGE="debian:12"
            echo "📥 Используем Debian 12"
            ;;
        3)
            BASE_IMAGE="ubuntu:22.04"
            echo "📥 Используем Ubuntu 22.04 LTS"
            ;;
        4)
            BASE_IMAGE="ubuntu:24.04"
            echo "📥 Используем Ubuntu 24.04 LTS"
            ;;
        5)
            # Пробуем загрузить Astra Linux
            ASTRA_IMAGE="registry.astralinux.ru/library/astra/ubi18@sha256:850a91072ae82fcd7c718e979d044bd8f4a218a1f7938c23d98d019e1b5e7bfa"
            if $CONTAINER_CMD pull "$ASTRA_IMAGE" 2>/dev/null; then
                BASE_IMAGE="$ASTRA_IMAGE"
                echo "📥 Используем Astra Linux из реестра"
            else
                echo "⚠️  Не удалось загрузить Astra Linux из реестра"
                echo "💡 Используем Debian 12 как альтернативу"
                BASE_IMAGE="debian:12"
            fi
            ;;
        6)
            # Используем образ Astra Linux с VNC из репозитория shinbatsu/astra-ui-vnc-container
            echo "📥 Настройка образа Astra Linux с VNC из репозитория..."
            echo ""
            if [ -f "$SCRIPT_DIR/setup-astra-vnc-image.sh" ]; then
                echo "💡 Запускаем скрипт setup-astra-vnc-image.sh..."
                bash "$SCRIPT_DIR/setup-astra-vnc-image.sh"
                if [ $? -eq 0 ]; then
                    # Используем готовый образ
                    BASE_IMAGE="localhost/astra-vnc:latest"
                    USE_VNC=true  # Принудительно включаем VNC
                    echo "✅ Образ готов: $BASE_IMAGE"
                    echo "💡 Этот образ уже содержит VNC, флаг --vnc включен автоматически"
                else
                    echo "❌ Не удалось настроить образ из репозитория"
                    echo "💡 Используем Debian 12 как альтернативу"
                    BASE_IMAGE="debian:12"
                fi
            else
                echo "❌ Скрипт setup-astra-vnc-image.sh не найден"
                echo "💡 Используем Debian 12 как альтернативу"
                BASE_IMAGE="debian:12"
            fi
            ;;
        7)
            read -p "Введите имя образа (например, debian:12): " BASE_IMAGE
            if [ -z "$BASE_IMAGE" ]; then
                echo "❌ Образ не указан, используем Debian 12"
                BASE_IMAGE="debian:12"
            fi
            ;;
        *)
            echo "❌ Неверный выбор, используем Debian 12"
            BASE_IMAGE="debian:12"
            ;;
    esac
fi

echo "📦 Базовый образ: $BASE_IMAGE"
echo ""

# Определяем дистрибутив из BASE_IMAGE для правильного тега
DISTRO_TAG="debian"  # По умолчанию
if echo "$BASE_IMAGE" | grep -qi "ubuntu"; then
    DISTRO_TAG="ubuntu"
elif echo "$BASE_IMAGE" | grep -qi "astra"; then
    DISTRO_TAG="astra"
fi

# Определяем имя образа
# Если используется готовый образ astra-vnc, используем его напрямую
if echo "$BASE_IMAGE" | grep -qi "astra-vnc"; then
    IMAGE_NAME="localhost/astra-vnc:latest"
    echo "✅ Используем готовый образ Astra Linux с VNC: $IMAGE_NAME"
    echo "💡 Образ уже содержит VNC и готов к использованию"
    echo ""
    echo "=================================================="
    echo "✅ Образ готов к использованию!"
    echo ""
    echo "📋 Информация об образе:"
    $CONTAINER_CMD images | grep -E "astra-vnc|REPOSITORY"
    echo ""
    echo "💡 Образ будет использоваться автоматически при выборе дистрибутива 'astra'"
    echo "   в настройках песочницы"
    echo "=================================================="
    exit 0
elif [ "$USE_VNC" = true ]; then
    IMAGE_TAG="vnc"
    # Новая схема именования: linux-gui-vnc:{distro}
    IMAGE_NAME="linux-gui-vnc:${DISTRO_TAG}"
    # Также создаем legacy тег для обратной совместимости
    IMAGE_NAME_LEGACY="linux-sandbox:vnc"
else
    IMAGE_TAG="base"
    # Новая схема именования: linux-base:{distro}
    IMAGE_NAME="linux-base:${DISTRO_TAG}"
    # Также создаем legacy тег для обратной совместимости
    IMAGE_NAME_LEGACY="linux-sandbox:base"
fi

echo "🔨 Создание образа контейнера для Linux Training Simulator"
echo "Контейнерная система: $CONTAINER_CMD"
echo "VNC: $([ "$USE_VNC" = true ] && echo "включен" || echo "выключен")"
echo "Дистрибутив: $DISTRO_TAG"
echo "Итоговый образ: localhost/$IMAGE_NAME"
if [ -n "$IMAGE_NAME_LEGACY" ]; then
    echo "Legacy тег (для совместимости): localhost/$IMAGE_NAME_LEGACY"
fi
echo ""

# Загрузка базового образа
echo "⬇️  Загрузка базового образа..."
if ! $CONTAINER_CMD pull "$BASE_IMAGE" 2>&1; then
    echo "❌ Не удалось загрузить образ: $BASE_IMAGE"
    echo "💡 Проверьте:"
    echo "   1. Интернет-соединение"
    echo "   2. Доступность образа: $BASE_IMAGE"
    echo "   3. Попробуйте другой образ: ./create-astra-image.sh --base debian:12"
    exit 1
fi
echo "✅ Базовый образ загружен"
echo ""

# Создание образа
if [ "$USE_VNC" = true ]; then
    echo "🔧 Создание образа с VNC..."
    
    # Проверка наличия Dockerfile
    DOCKERFILE="images/Dockerfile.astra-vnc"
    if [ ! -f "$DOCKERFILE" ]; then
        echo "❌ Файл $DOCKERFILE не найден"
        exit 1
    fi
    
    echo "📦 Сборка образа с VNC на базе $BASE_IMAGE..."
    if $CONTAINER_CMD build \
        --build-arg BASE_IMAGE="$BASE_IMAGE" \
        -t "localhost/$IMAGE_NAME" \
        -f "$DOCKERFILE" \
        . 2>&1; then
        echo ""
        echo "✅ Образ с VNC успешно создан: localhost/$IMAGE_NAME"
        # Создаем legacy тег для обратной совместимости
        if [ -n "$IMAGE_NAME_LEGACY" ]; then
            if $CONTAINER_CMD tag "localhost/$IMAGE_NAME" "localhost/$IMAGE_NAME_LEGACY" 2>&1; then
                echo "✅ Legacy тег создан: localhost/$IMAGE_NAME_LEGACY"
            fi
        fi
    else
        echo "❌ Ошибка при сборке образа"
        exit 1
    fi
else
    echo "🔧 Создание базового образа..."
    
    # Для базового образа просто тегируем загруженный образ
    echo "🏷️  Тегирование базового образа..."
    if $CONTAINER_CMD tag "$BASE_IMAGE" "localhost/$IMAGE_NAME" 2>&1; then
        echo "✅ Базовый образ создан: localhost/$IMAGE_NAME"
        # Создаем legacy тег для обратной совместимости
        if [ -n "$IMAGE_NAME_LEGACY" ]; then
            if $CONTAINER_CMD tag "localhost/$IMAGE_NAME" "localhost/$IMAGE_NAME_LEGACY" 2>&1; then
                echo "✅ Legacy тег создан: localhost/$IMAGE_NAME_LEGACY"
            fi
        fi
    else
        echo "❌ Ошибка при тегировании образа"
        exit 1
    fi
fi

# Показываем результат
echo ""
echo "📋 Доступные образы:"
$CONTAINER_CMD images | grep -E "REPOSITORY|localhost/linux-(gui-vnc|base|sandbox)" || $CONTAINER_CMD images | head -5

echo ""
echo "💡 Тестовый запуск:"
if [ "$USE_VNC" = true ]; then
    echo "   $CONTAINER_CMD run -d -p 5900:5900 -p 6080:6080 --name sandbox-test localhost/$IMAGE_NAME"
    echo ""
    echo "   Затем откройте в браузере:"
    echo "   http://localhost:6080/vnc.html"
    echo ""
    echo "   Для остановки:"
    echo "   $CONTAINER_CMD stop sandbox-test && $CONTAINER_CMD rm sandbox-test"
else
    echo "   $CONTAINER_CMD run --rm -it localhost/$IMAGE_NAME /bin/bash"
fi

echo ""
echo "✅ Готово!"
