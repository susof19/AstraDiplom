#!/bin/bash
# Универсальный скрипт быстрого старта для Debian-based систем
# Поддерживает: Debian, Ubuntu, Astra Linux, Linux Mint и другие Debian-based дистрибутивы
# Устанавливает все зависимости и запускает проект

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Определение пути к рабочему столу
if [ -d "$HOME/Рабочий стол" ]; then
    DESKTOP_DIR="$HOME/Рабочий стол"
elif [ -d "$HOME/Desktop" ]; then
    DESKTOP_DIR="$HOME/Desktop"
else
    DESKTOP_DIR="$HOME"
    echo "⚠️  Папка рабочего стола не найдена, ярлык будет создан в домашней директории"
fi

APP_NAME="Linux Training Simulator"

# Определение дистрибутива
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO_NAME="$NAME"
    DISTRO_ID="$ID"
else
    DISTRO_NAME="Unknown"
    DISTRO_ID="unknown"
fi

echo "🚀 Установка и запуск Linux Training Simulator"
echo "=================================================="
echo "Дистрибутив: $DISTRO_NAME"
echo ""

# Проверка прав root для установки пакетов
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Для установки пакетов требуются права администратора"
    echo "Скрипт будет запрашивать пароль при необходимости"
    echo ""
fi

# Отключение CD-репозитория если он мешает (актуально для некоторых дистрибутивов)
if grep -q "^deb cdrom:" /etc/apt/sources.list 2>/dev/null || \
   find /etc/apt/sources.list.d -name "*.list" -exec grep -q "^deb cdrom:" {} \; 2>/dev/null; then
    echo "🔧 Обнаружен CD-репозиторий, настраиваем использование только сетевых репозиториев..."
    if [ ! -f /etc/apt/apt.conf.d/99no-cdrom ]; then
        echo 'Acquire::cdrom::AutoDetect "false";' | sudo tee /etc/apt/apt.conf.d/99no-cdrom > /dev/null
        echo 'Acquire::cdrom::mount "/dev/null";' | sudo tee -a /etc/apt/apt.conf.d/99no-cdrom > /dev/null
        echo "✅ CD-репозиторий отключен для этой установки"
    fi
fi

# Функция для установки пакетов
install_package() {
    local package=$1
    if ! dpkg -l | grep -q "^ii.*$package"; then
        echo "📦 Установка $package..."
        
        # Обновляем список пакетов без CD-репозитория
        sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null || sudo apt-get update -qq
        
        # Пытаемся установить из сетевых репозиториев
        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
            -o Acquire::cdrom::AutoDetect=false \
            -o Acquire::cdrom::mount=/dev/null \
            --no-install-recommends \
            "$package" 2>&1 | grep -v "Смена носителя" || {
            echo "⚠️  Повторная попытка установки $package..."
            DEBIAN_FRONTEND=noninteractive sudo apt-get install -y "$package" || {
                echo "❌ Ошибка установки $package"
                echo "💡 Попробуйте установить вручную: sudo apt-get install $package"
                return 1
            }
        }
        echo "✅ $package установлен"
    else
        echo "✅ $package уже установлен"
    fi
}

# 1. Обновление списка пакетов
echo "📋 Обновление списка пакетов..."
sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null || \
sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true

# 2. Установка системных зависимостей
echo ""
echo "🔧 Установка системных зависимостей..."

# Python 3.10+
if ! command -v python3 &> /dev/null; then
    install_package "python3"
    install_package "python3-venv"
    install_package "python3-pip"
else
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✅ Python установлен: $(python3 --version)"
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
        echo "⚠️  Требуется Python 3.10+, текущая версия: $PYTHON_VERSION"
        install_package "python3"
        install_package "python3-venv"
        install_package "python3-pip"
    fi
fi

# Node.js 18+
if ! command -v node &> /dev/null; then
    echo "📦 Установка Node.js..."
    
    # Для разных дистрибутивов разные способы установки Node.js
    if [ "$DISTRO_ID" = "ubuntu" ] || [ "$DISTRO_ID" = "debian" ]; then
        # Используем NodeSource для Ubuntu/Debian
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        install_package "nodejs"
    else
        # Для других дистрибутивов пробуем стандартный способ
        install_package "nodejs"
        if ! command -v node &> /dev/null || [ "$(node --version | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
            echo "⚠️  Node.js не установлен или версия < 18"
            echo "💡 Установите Node.js 18+ вручную: https://nodejs.org/"
        fi
    fi
else
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo "⚠️  Требуется Node.js 18+, текущая версия: $(node --version)"
        echo "💡 Обновите Node.js: https://nodejs.org/"
    else
        echo "✅ Node.js установлен: $(node --version)"
    fi
fi

# npm
if ! command -v npm &> /dev/null; then
    install_package "npm"
else
    echo "✅ npm установлен: $(npm --version)"
fi

# Podman или Docker
if ! command -v podman &> /dev/null && ! command -v docker &> /dev/null; then
    echo "📦 Установка Podman..."
    # Пробуем установить podman
    if install_package "podman"; then
        echo "✅ Podman установлен"
    else
        # Если podman недоступен, пробуем docker
        echo "⚠️  Podman недоступен, пробуем Docker..."
        if install_package "docker.io"; then
            echo "✅ Docker установлен (будет использоваться вместо Podman)"
            # Добавляем пользователя в группу docker
            sudo usermod -aG docker "$USER" 2>/dev/null || true
        else
            echo "❌ Не удалось установить ни Podman, ни Docker"
            echo "💡 Установите вручную:"
            echo "   sudo apt-get install podman"
            echo "   или"
            echo "   sudo apt-get install docker.io"
        fi
    fi
else
    if command -v podman &> /dev/null; then
        echo "✅ Podman установлен: $(podman --version)"
    else
        echo "✅ Docker установлен: $(docker --version)"
        # Добавляем пользователя в группу docker
        sudo usermod -aG docker "$USER" 2>/dev/null || true
    fi
fi

# Дополнительные зависимости
install_package "curl"
install_package "wget"
install_package "git"
install_package "build-essential"

# 3. Настройка Backend
echo ""
echo "🐍 Настройка Python Backend..."
cd "$PROJECT_ROOT/backend"

if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения Python..."
    python3 -m venv venv
fi

echo "📦 Установка Python зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "✅ Backend настроен"

# 4. Настройка Frontend
echo ""
echo "🌐 Настройка React Frontend..."
cd "$PROJECT_ROOT/frontend/web"

if [ ! -d "node_modules" ]; then
    echo "📦 Установка Node.js зависимостей..."
    npm install
else
    echo "📦 Обновление Node.js зависимостей..."
    npm install
fi

echo "✅ Frontend настроен"

# 5. Создание образов контейнеров (опционально)
echo ""
read -p "Создать образы контейнеров для песочниц? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔨 Создание образов контейнеров..."
    echo "Выберите тип образа для создания:"
    echo "  1) Базовый образ (для CLI-миссий B, C)"
    echo "  2) Образ с VNC (для GUI-миссий A)"
    echo "  3) Оба образа"
    echo "  4) Пропустить создание образа"
    read -p "Ваш выбор (1-4): " image_choice
    
    cd "$PROJECT_ROOT/scripts"
    case $image_choice in
        1)
            bash create-astra-image.sh || {
                echo "⚠️  Ошибка создания базового образа"
                echo "💡 Образ можно создать позже: cd scripts && ./create-astra-image.sh"
            }
            ;;
        2)
            bash create-astra-image.sh --vnc || {
                echo "⚠️  Ошибка создания VNC образа"
                echo "💡 Образ можно создать позже: cd scripts && ./create-astra-image.sh --vnc"
            }
            ;;
        3)
            bash create-astra-image.sh || echo "⚠️  Ошибка создания базового образа"
            bash create-astra-image.sh --vnc || echo "⚠️  Ошибка создания образа с VNC"
            ;;
        *)
            echo "Создание образа пропущено."
            ;;
    esac
    
    if [ $image_choice -ne 4 ]; then
        echo ""
        echo "📋 Созданные образы:"
        if command -v podman &> /dev/null; then
            podman images | grep -E "REPOSITORY|localhost" || podman images | head -5
        else
            docker images | grep -E "REPOSITORY|localhost" || docker images | head -5
        fi
        echo ""
        echo "💡 Для тестирования образа:"
        echo "   podman run -d -p 5900:5900 -p 6080:6080 --name test-vnc localhost/astra-linux:vnc"
    fi
fi

# 6. Создание скрипта запуска
echo ""
echo "📝 Создание скрипта запуска..."
cd "$PROJECT_ROOT"

cat > start-demo.sh << 'EOF'
#!/bin/bash
# Скрипт запуска Linux Training Simulator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

echo "🚀 Подготовка и запуск Linux Training Simulator"
echo "=================================================="
echo ""

# 1. Проверка и создание VNC образа (если не существует)
echo "⚙️  Проверка наличия VNC образа..."
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo "❌ Podman или Docker не найдены"
    exit 1
fi

if ! $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep -q "localhost/astra-linux:vnc"; then
    echo "⚠️  VNC образ не найден. Создаем его на базе Debian 12 (рекомендуется для демонстрации)."
    read -p "Нажмите Enter для создания VNC образа (Debian 12)..."
    cd "$PROJECT_ROOT/scripts"
    echo "2" | bash create-astra-image.sh --vnc || {
        echo "❌ Не удалось создать VNC образ. Демонстрация может быть ограничена."
        read -p "Продолжить без VNC образа? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    }
    cd "$PROJECT_ROOT"
else
    echo "✅ VNC образ 'localhost/astra-linux:vnc' уже существует."
fi

# 2. Запуск Backend
echo "🚀 Запуск Backend..."
cd "$PROJECT_ROOT/backend"
source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd "$PROJECT_ROOT"
echo "✅ Backend запущен (PID: $BACKEND_PID)"

# 3. Ожидание запуска Backend
echo "⏳ Ожидание запуска Backend (3 секунды)..."
sleep 3

# 4. Запуск Frontend
echo "🌐 Запуск Frontend..."
cd "$PROJECT_ROOT/frontend/web"
npm start &
FRONTEND_PID=$!
cd "$PROJECT_ROOT"
echo "✅ Frontend запущен (PID: $FRONTEND_PID)"

echo ""
echo "=================================================="
echo "✅ Демонстрация запущена!"
echo "   Frontend (браузер): http://localhost:3000"
echo "   Backend (API):      http://localhost:8000"
echo ""
echo "💡 Для остановки всех процессов нажмите Ctrl+C"
echo "=================================================="

# Ожидание сигнала для остановки
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo -e '\n🛑 Демонстрация остановлена.'; exit" INT TERM
wait
EOF

chmod +x start-demo.sh
echo "✅ Скрипт start-demo.sh создан"

echo ""
echo "=================================================="
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Запустите приложение:"
echo "      ./start-demo.sh"
echo ""
echo "   2. Или запустите вручную:"
echo "      # Backend:"
echo "      cd backend && source venv/bin/activate && python run.py"
echo ""
echo "      # Frontend (в другом терминале):"
echo "      cd frontend/web && npm start"
echo ""
echo "   3. Откройте в браузере: http://localhost:3000"
echo ""
echo "💡 Для создания образов контейнеров:"
echo "   cd scripts"
echo "   ./create-astra-image.sh          # Базовый"
echo "   ./create-astra-image.sh --vnc   # С VNC"
echo "=================================================="

