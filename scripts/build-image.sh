#!/bin/bash
# Скрипт сборки образа Astra Linux с GUI
# Требует базовый образ astra-linux:se (созданный через create-astra-image.sh)

set -e

echo "🔨 Сборка образа Astra Linux с GUI для тренажёра"

cd "$(dirname "$0")/../images"

# Проверка наличия базового образа
if ! podman images | grep -qE "astra-linux.*se|astra-linux.*base"; then
    echo "⚠️  Базовый образ astra-linux:se не найден"
    echo ""
    echo "Сначала создайте базовый образ:"
    echo "  cd scripts"
    echo "  sudo ./create-astra-image.sh"
    echo ""
    echo "Или используйте существующий образ Astra Linux"
    exit 1
fi

echo "Сборка образа с GUI..."
podman build -f Dockerfile.astra-gui -t astra-linux:latest .

echo "✅ Образ собран: astra-linux:latest"
echo ""
echo "Проверка образа:"
podman images | grep astra-linux

