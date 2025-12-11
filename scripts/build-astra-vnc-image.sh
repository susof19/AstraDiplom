#!/bin/bash
# Скрипт сборки образа Astra Linux с TigerVNC и noVNC

set -e

IMAGE_NAME="${IMAGE_NAME:-localhost/astra-linux:vnc}"
BASE_IMAGE="${BASE_IMAGE:-registry.astralinux.ru/library/astra/ubi18@sha256:850a91072ae82fcd7c718e979d044bd8f4a218a1f7938c23d98d019e1b5e7bfa}"
DOCKERFILE="${DOCKERFILE:-images/Dockerfile.astra-vnc}"

echo "🔨 Сборка образа Astra Linux с VNC поддержкой"
echo "Базовый образ: $BASE_IMAGE"
echo "Итоговый образ: $IMAGE_NAME"
echo ""

# Проверка наличия Dockerfile
if [ ! -f "$DOCKERFILE" ]; then
    echo "❌ Файл $DOCKERFILE не найден"
    exit 1
fi

# Проверка наличия необходимых файлов
REQUIRED_FILES=(
    "images/start-vnc.sh"
    "images/supervisord.conf"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Файл $file не найден"
        exit 1
    fi
done

# Проверка установки podman
if ! command -v podman &> /dev/null; then
    echo "❌ Podman не установлен"
    echo "💡 Установите podman:"
    echo "   sudo apt install -y podman"
    exit 1
fi

# Сборка образа
echo "📦 Начинаем сборку образа..."
echo ""

podman build \
    --build-arg BASE_IMAGE="$BASE_IMAGE" \
    -t "$IMAGE_NAME" \
    -f "$DOCKERFILE" \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Образ успешно собран: $IMAGE_NAME"
    echo ""
    echo "📋 Информация об образе:"
    podman images | grep -E "REPOSITORY|astra-linux.*vnc" || podman images | head -2
    
    echo ""
    echo "💡 Тестовый запуск:"
    echo "   podman run --rm -d -p 5900:5900 -p 6080:6080 --name astra-vnc-test $IMAGE_NAME"
    echo ""
    echo "   Затем откройте в браузере:"
    echo "   http://localhost:6080/vnc.html"
    echo ""
    echo "   Для остановки:"
    echo "   podman stop astra-vnc-test"
    echo ""
    
    # Тегируем также без localhost/ для совместимости
    podman tag "$IMAGE_NAME" "astra-linux:vnc" 2>/dev/null || true
    
else
    echo ""
    echo "❌ Ошибка при сборке образа"
    exit 1
fi

