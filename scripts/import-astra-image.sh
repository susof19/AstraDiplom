#!/bin/bash
# Скрипт импорта готового образа Astra Linux
# Используйте если создание образа через debootstrap не удаётся

set -e

IMAGE_NAME="${IMAGE_NAME:-astra-linux:se}"
IMAGE_FILE="${IMAGE_FILE:-}"

echo "📥 Импорт образа Astra Linux"
echo ""

if [ -z "$IMAGE_FILE" ]; then
    echo "Использование:"
    echo "  $0 <путь_к_файлу_образа.tar>"
    echo ""
    echo "Или установите переменную окружения:"
    echo "  IMAGE_FILE=/path/to/image.tar $0"
    exit 1
fi

if [ ! -f "$IMAGE_FILE" ]; then
    echo "❌ Файл образа не найден: $IMAGE_FILE"
    exit 1
fi

echo "Импорт образа из $IMAGE_FILE..."
podman import "$IMAGE_FILE" "$IMAGE_NAME" \
    --change "ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
    --change 'CMD ["/bin/bash"]' \
    --change "ENV LANG=ru_RU.UTF-8"

echo ""
echo "✅ Образ импортирован: $IMAGE_NAME"
echo ""
echo "Проверка образа:"
podman images | grep "$IMAGE_NAME"

echo ""
echo "Тестовый запуск:"
echo "podman run --rm -it $IMAGE_NAME /bin/bash"

