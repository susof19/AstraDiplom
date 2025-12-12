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

Результат:
  Базовый образ:  localhost/linux-sandbox:base
  Образ с VNC:    localhost/linux-sandbox:vnc

EOF
    exit 0
fi

# Определяем имя образа
if [ "$USE_VNC" = true ]; then
    IMAGE_TAG="vnc"
    IMAGE_NAME="linux-sandbox:vnc"
else
    IMAGE_TAG="base"
    IMAGE_NAME="linux-sandbox:base"
fi

echo "🔨 Создание образа контейнера для Linux Training Simulator"
echo "Контейнерная система: $CONTAINER_CMD"
echo "VNC: $([ "$USE_VNC" = true ] && echo "включен" || echo "выключен")"
echo "Итоговый образ: localhost/$IMAGE_NAME"
echo ""

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
    echo "  6) Указать свой образ"
    echo ""
    read -p "Выберите вариант (1-6): " -n 1 -r
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
    else
        echo "❌ Ошибка при тегировании образа"
        exit 1
    fi
fi

# Показываем результат
echo ""
echo "📋 Доступные образы:"
$CONTAINER_CMD images | grep -E "REPOSITORY|localhost/linux-sandbox|linux-sandbox" || $CONTAINER_CMD images | head -5

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
