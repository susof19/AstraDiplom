#!/bin/bash
# Скрипт для настройки образа Astra Linux с VNC из репозитория shinbatsu/astra-ui-vnc-container
# Использование: ./scripts/setup-astra-vnc-image.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMP_DIR="$PROJECT_ROOT/temp-astra-vnc"
REPO_URL="https://github.com/shinbatsu/astra-ui-vnc-container.git"
IMAGE_NAME="astra-vnc:latest"
LOCAL_IMAGE_NAME="localhost/astra-vnc:latest"

echo "🔧 Настройка образа Astra Linux с VNC"
echo "=================================================="
echo ""

# Определяем команду контейнера (docker или podman)
CONTAINER_CMD=""
if command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
else
    echo "❌ Не найдена команда docker или podman"
    echo "💡 Установите Docker или Podman для продолжения"
    exit 1
fi

echo "✅ Используем: $CONTAINER_CMD"
echo ""

# Проверяем, существует ли уже образ
if $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${LOCAL_IMAGE_NAME}\|^${IMAGE_NAME}\|^localhost/${IMAGE_NAME}"; then
    echo "📦 Образ уже существует:"
    $CONTAINER_CMD images | grep -E "astra-vnc|REPOSITORY"
    echo ""
    read -p "Пересобрать образ? (y/N): " REBUILD
    if [[ ! "$REBUILD" =~ ^[Yy]$ ]]; then
        echo "✅ Используем существующий образ"
        exit 0
    fi
fi

# Проверяем наличие локальных файлов в images/
IMAGES_DIR="$PROJECT_ROOT/images"
if [ -f "$IMAGES_DIR/Dockerfile.vnc" ] && [ -f "$IMAGES_DIR/Dockerfile.fly" ]; then
    echo "📦 Используем локальные файлы из images/..."
    USE_LOCAL_FILES=true
    BUILD_DIR="$IMAGES_DIR"
else
    # Клонируем репозиторий, если локальные файлы отсутствуют
    echo "📥 Локальные файлы не найдены, клонирование репозитория..."
    if [ -d "$TEMP_DIR" ]; then
        echo "   Удаляем старую директорию..."
        rm -rf "$TEMP_DIR"
    fi
    
    if ! command -v git &> /dev/null; then
        echo "❌ Git не установлен"
        echo "💡 Установите git: sudo apt-get install git"
        exit 1
    fi
    
    git clone "$REPO_URL" "$TEMP_DIR" || {
        echo "❌ Не удалось клонировать репозиторий"
        echo "💡 Проверьте подключение к интернету и доступность GitHub"
        exit 1
    }
    
    echo "✅ Репозиторий клонирован"
    USE_LOCAL_FILES=false
    BUILD_DIR="$TEMP_DIR"
fi
echo ""

# Переходим в директорию для сборки
cd "$BUILD_DIR"

# Проверяем наличие Dockerfile.vnc (обязательный)
if [ ! -f "Dockerfile.vnc" ]; then
    echo "❌ Dockerfile.vnc не найден"
    echo "💡 Проверьте наличие файлов в $BUILD_DIR"
    if [ "$USE_LOCAL_FILES" = false ]; then
        rm -rf "$TEMP_DIR"
    fi
    exit 1
fi

# Убеждаемся, что entrypoint.sh существует
if [ ! -f ".scripts/entrypoint.sh" ]; then
    echo "🔧 Создание entrypoint.sh..."
    mkdir -p .scripts
    # Если есть в scripts/, копируем оттуда, иначе создаем базовый
    if [ -f "scripts/entrypoint.sh" ]; then
        cp scripts/entrypoint.sh .scripts/entrypoint.sh
        echo "✅ entrypoint.sh скопирован из scripts/"
    elif [ -f "$IMAGES_DIR/.scripts/entrypoint.sh" ]; then
        cp "$IMAGES_DIR/.scripts/entrypoint.sh" .scripts/entrypoint.sh
        echo "✅ entrypoint.sh скопирован из images/.scripts/"
    else
        echo "⚠️  entrypoint.sh не найден, будет создан при сборке"
    fi
    echo ""
fi

# Убеждаемся, что xorg.conf существует
if [ ! -f "xorg.conf" ] && [ -f "$IMAGES_DIR/xorg.conf" ]; then
    echo "🔧 Копирование xorg.conf..."
    cp "$IMAGES_DIR/xorg.conf" xorg.conf
    echo "✅ xorg.conf скопирован"
    echo ""
fi

echo "📦 Сборка образов Astra Linux..."
echo "   Это может занять несколько минут..."
echo ""

# Сначала собираем базовый образ astra-fly (если Dockerfile.fly существует)
FLY_IMAGE="astra-fly:v1.7.6"
if [ -f "Dockerfile.fly" ]; then
    echo "🔨 Шаг 1/2: Сборка базового образа $FLY_IMAGE..."
    if $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${FLY_IMAGE}\|^localhost/${FLY_IMAGE}"; then
        echo "✅ Базовый образ $FLY_IMAGE уже существует, пропускаем сборку"
    else
        if $CONTAINER_CMD build -f Dockerfile.fly -t "$FLY_IMAGE" .; then
            echo "✅ Базовый образ $FLY_IMAGE собран"
        else
            echo ""
            echo "❌ Ошибка при сборке базового образа"
            echo "💡 Проверьте логи выше для деталей"
            rm -rf "$TEMP_DIR"
            exit 1
        fi
    fi
    echo ""
else
    echo "⚠️  Dockerfile.fly не найден, пропускаем сборку базового образа"
    echo "💡 Попытаемся собрать astra-vnc напрямую (может потребоваться базовый образ из реестра)"
    echo ""
fi

# Затем собираем образ с VNC, который использует базовый образ
if [ -f "Dockerfile.fly" ]; then
    echo "🔨 Шаг 2/2: Сборка образа с VNC (использует $FLY_IMAGE)..."
else
    echo "🔨 Сборка образа с VNC..."
fi

# Исправляем путь к entrypoint.sh в Dockerfile.vnc, если он указывает на .scripts/entrypoint.sh
# Это нужно, если Dockerfile.vnc был взят из репозитория, где entrypoint.sh находится в scripts/
if grep -q "ADD \.scripts/entrypoint.sh" Dockerfile.vnc 2>/dev/null; then
    echo "🔧 Путь к entrypoint.sh уже корректный"
fi

if $CONTAINER_CMD build -f Dockerfile.vnc -t "$LOCAL_IMAGE_NAME" .; then
    echo ""
    echo "✅ Образ успешно собран: $LOCAL_IMAGE_NAME"
    echo ""
    echo "⚠️  ВАЖНО: Если у вас есть запущенные контейнеры с старым образом, остановите их:"
    echo "   $CONTAINER_CMD ps | grep astra-vnc"
    echo "   $CONTAINER_CMD stop <container_id>"
    echo "   $CONTAINER_CMD rm <container_id>"
else
    echo ""
    echo "❌ Ошибка при сборке образа с VNC"
    echo ""
    echo "💡 Возможные причины:"
    echo "   1. Отсутствуют необходимые файлы в репозитории (например, scripts/entrypoint.sh)"
    echo "   2. Базовый образ astra-fly:v1.7.6 недоступен"
    echo "   3. Недостаточно прав для сборки образа"
    echo "   4. Ошибка в Dockerfile.vnc (неправильные пути к файлам)"
    echo ""
    echo "💡 Решения:"
    echo "   1. Проверить структуру репозитория:"
    echo "      ls -la $TEMP_DIR"
    echo "      ls -la $TEMP_DIR/scripts/"
    echo "   2. Использовать наш собственный Dockerfile для Astra Linux (рекомендуется):"
    echo "      cd $PROJECT_ROOT"
    echo "      ./scripts/create-astra-image.sh --vnc"
    echo "   3. Проверить Dockerfile.vnc: cat $TEMP_DIR/Dockerfile.vnc"
    echo ""
    echo "⚠️  Обратите внимание: Репозиторий shinbatsu/astra-ui-vnc-container использует"
    echo "   приватный базовый образ, который недоступен публично."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Также создаем тег без localhost/ для совместимости
if [ "$CONTAINER_CMD" = "podman" ]; then
    $CONTAINER_CMD tag "$LOCAL_IMAGE_NAME" "$IMAGE_NAME" 2>/dev/null || true
fi

# Очищаем временную директорию (только если использовали клонирование)
if [ "$USE_LOCAL_FILES" = false ]; then
    echo ""
    echo "🧹 Очистка временных файлов..."
    rm -rf "$TEMP_DIR"
fi

echo ""
echo "=================================================="
echo "✅ Образ Astra Linux с VNC готов к использованию!"
echo ""
echo "📋 Информация об образе:"
$CONTAINER_CMD images | grep -E "astra-vnc|REPOSITORY"
echo ""
echo "💡 Образ будет использоваться автоматически при выборе дистрибутива 'astra'"
echo "   в настройках песочницы"
echo "=================================================="

