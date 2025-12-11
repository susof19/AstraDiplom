#!/bin/bash
# Скрипт создания образа Astra Linux в rootless режиме (без sudo)
# Использует готовый образ из реестра Astra Linux

set -e

IMAGE_NAME="${IMAGE_NAME:-astra-linux:se}"
FALLBACK_IMAGE="${FALLBACK_IMAGE:-registry.astralinux.ru/library/astra/ubi18@sha256:850a91072ae82fcd7c718e979d044bd8f4a218a1f7938c23d98d019e1b5e7bfa}"

echo "🔨 Создание образа Astra Linux (rootless режим)"
echo "Образ: $IMAGE_NAME"
echo "Источник: $FALLBACK_IMAGE"
echo ""

# Проверяем, установлен ли podman
if ! command -v podman &> /dev/null; then
    echo "❌ Podman не установлен"
    echo "💡 Установите podman:"
    echo "   sudo apt install -y podman"
    exit 1
fi

# Проверяем, есть ли уже образ
echo "🔍 Проверка существующих образов..."
if podman images | grep -q "$IMAGE_NAME"; then
    echo "⚠️  Образ $IMAGE_NAME уже существует"
    echo ""
    podman images | grep -E "REPOSITORY|$IMAGE_NAME"
    echo ""
    read -p "Пересоздать образ? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Отменено"
        exit 0
    fi
    
    # Удаляем старый образ
    echo "🗑️  Удаление старого образа..."
    podman rmi "localhost/$IMAGE_NAME" 2>/dev/null || true
    podman rmi "$IMAGE_NAME" 2>/dev/null || true
fi

# Загружаем образ из реестра
echo ""
echo "📥 Загрузка образа из реестра Astra Linux..."
echo "Это может занять несколько минут..."
echo ""

if podman pull "$FALLBACK_IMAGE"; then
    echo ""
    echo "✅ Образ загружен из реестра"
    
    # Тегируем образ с нужным именем
    echo "🏷️  Тегирование образа..."
    podman tag "$FALLBACK_IMAGE" "localhost/$IMAGE_NAME"
    podman tag "$FALLBACK_IMAGE" "$IMAGE_NAME" 2>/dev/null || true
    
    echo ""
    echo "✅ Образ создан: localhost/$IMAGE_NAME"
    echo ""
    echo "📋 Доступные образы:"
    podman images | grep -E "REPOSITORY|$IMAGE_NAME|localhost/$IMAGE_NAME" || podman images
    
    echo ""
    echo "💡 Тестовый запуск:"
    echo "   podman run --rm -it localhost/$IMAGE_NAME /bin/bash"
    
    echo ""
    echo "📝 Информация об образе:"
    podman inspect "localhost/$IMAGE_NAME" --format='Теги: {{.RepoTags}}' 2>/dev/null || true
    
else
    echo ""
    echo "❌ Не удалось загрузить образ из реестра"
    echo ""
    echo "💡 Возможные причины:"
    echo "   1. Нет доступа к интернету"
    echo "   2. Реестр недоступен"
    echo "   3. Неверный URL образа"
    echo ""
    echo "💡 Попробуйте альтернативные варианты:"
    echo ""
    echo "   # Вариант 1: Официальный образ Astra Linux 1.8"
    echo "   podman pull registry.astralinux.ru/library/astra/ubi18:1.8.1"
    echo "   podman tag registry.astralinux.ru/library/astra/ubi18:1.8.1 localhost/$IMAGE_NAME"
    echo ""
    echo "   # Вариант 2: Базовый образ Debian (для тестирования)"
    echo "   podman pull debian:12"
    echo "   podman tag debian:12 localhost/$IMAGE_NAME"
    echo ""
    echo "   # Вариант 3: Создание через debootstrap (требует sudo)"
    echo "   sudo ./create-astra-image.sh"
    echo ""
    exit 1
fi
