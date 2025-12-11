#!/bin/bash
# Скрипт проверки готовности к созданию образов

echo "🔍 Проверка готовности к созданию образов Astra Linux"
echo "=================================================="
echo ""

# Переходим в корень проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Корневая директория проекта: $PROJECT_ROOT"
echo ""

# Проверка podman
echo "1. Проверка Podman..."
if command -v podman &> /dev/null; then
    echo "   ✅ Podman установлен: $(podman --version)"
else
    echo "   ❌ Podman не установлен"
    echo "   💡 Установите: sudo apt install podman"
fi
echo ""

# Проверка файлов для VNC образа
echo "2. Проверка файлов для VNC образа..."
VNC_FILES=(
    "images/Dockerfile.astra-vnc"
    "images/start-vnc.sh"
    "images/supervisord.conf"
)

ALL_VNC_OK=true
for file in "${VNC_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file - НЕ НАЙДЕН"
        ALL_VNC_OK=false
    fi
done

if [ "$ALL_VNC_OK" = true ]; then
    echo "   ✅ Все файлы для VNC образа на месте"
else
    echo "   ⚠️  Некоторые файлы отсутствуют"
fi
echo ""

# Проверка доступности реестра
echo "3. Проверка доступности реестра Astra Linux..."
if curl -s -I https://registry.astralinux.ru/ > /dev/null 2>&1; then
    echo "   ✅ Реестр доступен"
else
    echo "   ⚠️  Реестр недоступен (может потребоваться VPN или прокси)"
fi
echo ""

# Проверка существующих образов
echo "4. Проверка существующих образов..."
if podman images | grep -q "astra-linux"; then
    echo "   ✅ Образы Astra Linux найдены:"
    podman images | grep "astra-linux" | sed 's/^/      /'
else
    echo "   ℹ️  Образы Astra Linux не найдены"
    echo "   💡 Создайте образы командой:"
    echo "      cd scripts"
    echo "      ./create-astra-image.sh --vnc"
fi
echo ""

# Проверка миссий
echo "5. Проверка миссий..."
MISSIONS_COUNT=$(find missions -name "mission.yaml" | wc -l)
echo "   ✅ Найдено миссий: $MISSIONS_COUNT"
echo ""

# Итоговая рекомендация
echo "=================================================="
echo ""
if [ "$ALL_VNC_OK" = true ] && command -v podman &> /dev/null; then
    echo "✅ Система готова к созданию образов!"
    echo ""
    echo "Для создания образов выполните:"
    echo "  cd scripts"
    echo "  ./create-astra-image.sh          # Базовый образ"
    echo "  ./create-astra-image.sh --vnc    # Образ с VNC"
else
    echo "⚠️  Требуется настройка"
    echo ""
    if ! command -v podman &> /dev/null; then
        echo "1. Установите Podman:"
        echo "   sudo apt install podman"
    fi
    if [ "$ALL_VNC_OK" = false ]; then
        echo "2. Проверьте наличие файлов в папке images/"
    fi
fi

