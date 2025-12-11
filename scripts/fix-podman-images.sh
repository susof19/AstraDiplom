#!/bin/bash
# Скрипт для переноса образа из root podman в rootless podman
# Решает проблему, когда образ создан через sudo, но не виден пользователю

set -e

IMAGE_NAME="${IMAGE_NAME:-astra-linux:se}"
TEMP_TAR="/tmp/astra-linux-export-$(date +%s).tar"

echo "🔧 Исправление доступа к образам Podman"
echo "Образ: $IMAGE_NAME"
echo ""

# Проверяем, есть ли образ у root
echo "🔍 Проверка образа у root..."
if sudo podman images | grep -q "$IMAGE_NAME"; then
    echo "✅ Образ найден у root"
    
    # Экспортируем образ
    echo "📦 Экспорт образа из root podman..."
    sudo podman save -o "$TEMP_TAR" "localhost/$IMAGE_NAME" || sudo podman save -o "$TEMP_TAR" "$IMAGE_NAME"
    
    # Меняем владельца
    echo "🔑 Изменение владельца файла..."
    sudo chown $(id -u):$(id -g) "$TEMP_TAR"
    
    # Импортируем для текущего пользователя
    echo "📥 Импорт образа в rootless podman..."
    podman load -i "$TEMP_TAR"
    
    # Тегируем с правильным именем
    echo "🏷️  Тегирование образа..."
    IMAGE_ID=$(podman images --format '{{.ID}}' | head -1)
    podman tag "$IMAGE_ID" "localhost/$IMAGE_NAME"
    podman tag "$IMAGE_ID" "$IMAGE_NAME" 2>/dev/null || true
    
    # Удаляем временный файл
    echo "🧹 Очистка..."
    rm -f "$TEMP_TAR"
    
    echo ""
    echo "✅ Образ успешно перенесён!"
    echo ""
    echo "📋 Доступные образы:"
    podman images
    
    echo ""
    echo "💡 Тестовый запуск:"
    echo "   podman run --rm -it localhost/$IMAGE_NAME /bin/bash"
    
else
    echo "❌ Образ не найден у root"
    echo ""
    echo "💡 Попробуйте создать образ заново:"
    echo "   sudo ./create-astra-image.sh"
    echo ""
    echo "   Или используйте rootless версию:"
    echo "   ./create-astra-image-rootless.sh"
    exit 1
fi
