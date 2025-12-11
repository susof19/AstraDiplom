#!/bin/bash
# Скрипт загрузки готового образа Astra Linux из реестра
# Используется как fallback если создание образа не удаётся

set -e

IMAGE_NAME="${IMAGE_NAME:-astra-linux:se}"
REGISTRY_IMAGE="${REGISTRY_IMAGE:-registry.astralinux.ru/library/astra/ubi18:1.8.1}"

echo "📥 Загрузка образа Astra Linux из реестра"
echo "Реестр: $REGISTRY_IMAGE"
echo "Локальное имя: $IMAGE_NAME"
echo ""

# Проверка доступности podman
if ! command -v podman &> /dev/null; then
    echo "❌ Podman не установлен"
    exit 1
fi

# Попытка загрузки образа
echo "Загрузка образа (это может занять некоторое время)..."
if podman pull "$REGISTRY_IMAGE"; then
    echo "✅ Образ загружен из реестра"
    
    # Тегируем образ с нужным именем (используем localhost/ для локальных образов)
    podman tag "$REGISTRY_IMAGE" "localhost/$IMAGE_NAME"
    podman tag "$REGISTRY_IMAGE" "$IMAGE_NAME" 2>/dev/null || true
    echo "✅ Образ помечен как localhost/$IMAGE_NAME и $IMAGE_NAME"
    
    echo ""
    echo "Проверка образа:"
    podman images | grep -E "REPOSITORY|$IMAGE_NAME|$REGISTRY_IMAGE" || podman images
    
    echo ""
    echo "✅ Образ готов к использованию: localhost/$IMAGE_NAME"
    echo ""
    echo "💡 Тестовый запуск:"
    echo "   podman run --rm -it localhost/$IMAGE_NAME /bin/bash"
else
    echo "❌ Не удалось загрузить образ из реестра"
    echo "💡 Возможные причины:"
    echo "   - Нет доступа к реестру registry.astralinux.ru"
    echo "   - Требуется аутентификация"
    echo "   - Образ недоступен по указанному адресу"
    echo ""
    echo "💡 Попробуйте:"
    echo "   1. Проверить доступность реестра: curl -I https://registry.astralinux.ru"
    echo "   2. Создать образ через debootstrap: ./create-astra-image.sh"
    echo "   3. Использовать локальный образ: ./import-astra-image.sh <путь>"
    exit 1
fi

