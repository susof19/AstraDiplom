#!/bin/bash
# Скрипт создания образа Astra Linux для тренажёра
# Поддерживает создание базового образа и образа с VNC

set -e

# Параметры по умолчанию
USE_VNC=false
USE_SUDO=false
USE_ROOTLESS=true
SHOW_HELP=false

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
        --with-sudo)
            USE_SUDO=true
            USE_ROOTLESS=false
            shift
            ;;
        --rootless)
            USE_ROOTLESS=true
            USE_SUDO=false
            shift
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
    cat << 'EOF'
Использование: ./create-astra-image.sh [OPTIONS]

Создание образа Astra Linux для тренажёра

Опции:
  --vnc              Создать образ с VNC поддержкой (TigerVNC + noVNC + XFCE)
  --no-vnc           Создать базовый образ без VNC (по умолчанию)
  --rootless         Использовать rootless режим - загрузка из реестра (по умолчанию)
  --with-sudo        Использовать sudo для создания через debootstrap
  --help, -h         Показать эту справку

Примеры:
  # Создать базовый образ (для CLI-миссий)
  ./create-astra-image.sh

  # Создать образ с VNC (для GUI-миссий)
  ./create-astra-image.sh --vnc

  # Создать через debootstrap (требует sudo)
  sudo ./create-astra-image.sh --with-sudo --vnc

Результат:
  Базовый образ:  localhost/astra-linux:se
  Образ с VNC:    localhost/astra-linux:vnc

EOF
    exit 0
fi

# Определяем имя образа
if [ "$USE_VNC" = true ]; then
    IMAGE_TAG="vnc"
    IMAGE_NAME="astra-linux:vnc"
else
    IMAGE_TAG="se"
    IMAGE_NAME="astra-linux:se"
fi

echo "🔨 Создание образа Astra Linux для тренажёра"
echo "Режим: $([ "$USE_ROOTLESS" = true ] && echo "rootless (из реестра)" || echo "с sudo (debootstrap)")"
echo "VNC: $([ "$USE_VNC" = true ] && echo "включен" || echo "выключен")"
echo "Итоговый образ: localhost/$IMAGE_NAME"
echo ""

# ROOTLESS РЕЖИМ - загрузка из реестра и сборка с VNC
if [ "$USE_ROOTLESS" = true ]; then
    echo "📥 Режим rootless: загрузка базового образа из реестра..."
    
    FALLBACK_IMAGE="registry.astralinux.ru/library/astra/ubi18@sha256:850a91072ae82fcd7c718e979d044bd8f4a218a1f7938c23d98d019e1b5e7bfa"
    
    # Проверка podman
    if ! command -v podman &> /dev/null; then
        echo "❌ Podman не установлен"
        echo "💡 Установите podman:"
        echo "   sudo apt install -y podman"
        exit 1
    fi
    
    if [ "$USE_VNC" = true ]; then
        echo "🔧 Создание образа с VNC..."
        echo ""
        echo "⚠️  Внимание: Базовый образ Astra Linux не содержит GUI пакетов"
        echo ""
        echo "Выберите вариант:"
        echo "  1) Упрощённая версия (без реального VNC, только для демонстрации)"
        echo "  2) Использовать Debian 12 как базу (для тестирования с полным VNC)"
        echo "  3) Отмена"
        echo ""
        read -p "Выберите вариант (1-3): " -n 1 -r
        echo
        echo ""
        
        # Переходим в корень проекта
        cd "$(dirname "$0")/.."
        
        case $REPLY in
            1)
                echo "📦 Сборка упрощённой версии..."
                
                # Проверка файлов
                if [ ! -f "images/Dockerfile.astra-vnc-simple" ]; then
                    echo "❌ Файл images/Dockerfile.astra-vnc-simple не найден"
                    exit 1
                fi

                # Сборка
                podman build \
                    --build-arg BASE_IMAGE="$FALLBACK_IMAGE" \
                    -t "localhost/$IMAGE_NAME" \
                    -f images/Dockerfile.astra-vnc-simple \
                    .
                
                if [ $? -eq 0 ]; then
                    echo ""
                    echo "✅ Упрощённый образ создан"
                    echo "⚠️  Это демонстрационная версия без реального VNC"
                    echo "💡 Для CLI-миссий используйте базовый образ: ./create-astra-image.sh"
                fi
                ;;
            2)
                echo "📥 Загрузка Debian 12 как базового образа..."
                
                if podman pull debian:12; then
                    echo "✅ Debian 12 загружен"
                    
                    # Проверка файлов
                    if [ ! -f "images/Dockerfile.astra-vnc" ]; then
                        echo "❌ Файл images/Dockerfile.astra-vnc не найден"
                        exit 1
                    fi
                    
                    echo "📦 Сборка образа с VNC на базе Debian..."
                    podman build \
                        --build-arg BASE_IMAGE="debian:12" \
                        -t "localhost/$IMAGE_NAME" \
                        -f images/Dockerfile.astra-vnc \
                        .
                    
                    if [ $? -eq 0 ]; then
                        echo ""
                        echo "✅ Образ с VNC создан на базе Debian 12"
                        echo "💡 Это тестовая версия для разработки"
                    fi
                else
                    echo "❌ Не удалось загрузить Debian 12"
                    exit 1
                fi
                ;;
            3)
                echo "Отменено"
                exit 0
                ;;
            *)
                echo "❌ Неверный выбор"
                exit 1
                ;;
        esac
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Образ с VNC успешно создан: localhost/$IMAGE_NAME"
        else
            echo "❌ Ошибка при сборке образа"
            exit 1
        fi
        
    else
        echo "📥 Загрузка базового образа из реестра..."
        
        if podman pull "$FALLBACK_IMAGE"; then
            echo "✅ Образ загружен из реестра"
            
            # Тегируем образ
            echo "🏷️  Тегирование образа..."
            podman tag "$FALLBACK_IMAGE" "localhost/$IMAGE_NAME"
            podman tag "$FALLBACK_IMAGE" "$IMAGE_NAME" 2>/dev/null || true
            
            echo ""
            echo "✅ Базовый образ создан: localhost/$IMAGE_NAME"
        else
            echo "❌ Не удалось загрузить образ из реестра"
            echo "💡 Проверьте доступность реестра:"
            echo "   1. Проверьте интернет-соединение"
            echo "   2. Попробуйте: podman pull registry.astralinux.ru/library/astra/ubi18:1.8.1"
            echo "   3. Или используйте альтернативный образ: podman pull debian:12"
            exit 1
        fi
    fi
    
    # Возвращаемся в исходную директорию
    cd - > /dev/null 2>&1 || true
    
    # Показываем результат
    echo ""
    echo "📋 Доступные образы:"
    podman images | grep -E "REPOSITORY|astra-linux" || podman images | head -5
        
        echo ""
    echo "💡 Тестовый запуск:"
    if [ "$USE_VNC" = true ]; then
        echo "   podman run -d -p 5900:5900 -p 6080:6080 --name astra-test localhost/$IMAGE_NAME"
        echo ""
        echo "   Затем откройте в браузере:"
        echo "   http://localhost:6080/vnc.html"
    else
        echo "   podman run --rm -it localhost/$IMAGE_NAME /bin/bash"
    fi
    
    exit 0
fi

# РЕЖИМ С SUDO - создание через debootstrap (старый код)
echo "⚠️  Режим с sudo: создание через debootstrap"
echo "💡 Рекомендуется использовать rootless режим без sudo"
echo ""

# Проверка прав
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Для режима --with-sudo требуются права root"
    echo "💡 Запустите: sudo $0 --with-sudo"
    exit 1
fi

# Остальной код для debootstrap...
echo "❌ Режим debootstrap временно недоступен"
echo "💡 Используйте rootless режим:"
echo "   ./create-astra-image.sh $([ "$USE_VNC" = true ] && echo "--vnc" || echo "")"
exit 1
