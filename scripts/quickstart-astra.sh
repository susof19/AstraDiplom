#!/bin/bash
# Скрипт быстрого старта для Astra Linux
# Устанавливает все зависимости и запускает проект

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Определение пути к рабочему столу (Astra Linux может использовать русское название)
if [ -d "$HOME/Рабочий стол" ]; then
    DESKTOP_DIR="$HOME/Рабочий стол"
elif [ -d "$HOME/Desktop" ]; then
    DESKTOP_DIR="$HOME/Desktop"
else
    DESKTOP_DIR="$HOME"
    echo "⚠️  Папка рабочего стола не найдена, ярлык будет создан в домашней директории"
fi

APP_NAME="Astra Linux Trainer"

echo "🚀 Установка и запуск Astra Linux Training Simulator"
echo "=================================================="
echo ""

# Проверка прав root для установки пакетов
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Для установки пакетов требуются права администратора"
    echo "Скрипт будет запрашивать пароль при необходимости"
    echo ""
fi

# Отключение CD-репозитория если он мешает
if grep -q "^deb cdrom:" /etc/apt/sources.list 2>/dev/null || \
   find /etc/apt/sources.list.d -name "*.list" -exec grep -q "^deb cdrom:" {} \; 2>/dev/null; then
    echo "🔧 Обнаружен CD-репозиторий, настраиваем использование только сетевых репозиториев..."
    if [ ! -f /etc/apt/apt.conf.d/99no-cdrom ]; then
        echo 'Acquire::cdrom::AutoDetect "false";' | sudo tee /etc/apt/apt.conf.d/99no-cdrom > /dev/null
        echo 'Acquire::cdrom::mount "/dev/null";' | sudo tee -a /etc/apt/apt.conf.d/99no-cdrom > /dev/null
        echo "✅ CD-репозиторий отключен для этой установки"
    fi
fi

# Игнорирование ошибок с репозиториями при обновлении
echo "📋 Обновление списка пакетов..."
sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null || \
sudo apt-get update -qq 2>&1 | grep -vE "(Смена носителя|Release|не содержит)" || {
    echo "⚠️  Некоторые репозитории недоступны, продолжаем..."
    true
}

# Функция для установки пакетов
install_package() {
    local package=$1
    if ! dpkg -l | grep -q "^ii.*$package"; then
        echo "📦 Установка $package..."
        
        # Обновляем список пакетов без CD-репозитория
        sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null || sudo apt-get update -qq
        
        # Пытаемся установить из сетевых репозиториев
        # Используем DEBIAN_FRONTEND=noninteractive чтобы избежать запросов о CD
        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
            -o Acquire::cdrom::AutoDetect=false \
            -o Acquire::cdrom::mount=/dev/null \
            --no-install-recommends \
            "$package" 2>&1 | grep -v "Смена носителя" || {
            # Если не получилось, пробуем без опций CD
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
# Пытаемся обновить без CD-репозитория
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
    fi
fi

# Node.js 18+
if ! command -v node &> /dev/null; then
    echo "📦 Установка Node.js..."
    # Проверяем наличие NodeSource репозитория
    if [ ! -f /etc/apt/sources.list.d/nodesource.list ]; then
        echo "Добавление репозитория NodeSource..."
        # Добавляем репозиторий с игнорированием CD
        curl -fsSL https://deb.nodesource.com/setup_18.x | \
            sudo -E bash - 2>&1 | grep -v "Смена носителя" || true
        
        # Обновляем список пакетов после добавления репозитория
        sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null || \
        sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true
    fi
    
    # Устанавливаем Node.js с игнорированием CD
    echo "Установка nodejs из сетевых репозиториев..."
    DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
        -o Acquire::cdrom::AutoDetect=false \
        -o Acquire::cdrom::mount=/dev/null \
        nodejs 2>&1 | grep -v "Смена носителя" || {
        echo "⚠️  Попытка установки без опций CD..."
        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y nodejs
    }
    
    if command -v node &> /dev/null; then
        echo "✅ Node.js установлен: $(node --version)"
    else
        echo "❌ Не удалось установить Node.js автоматически"
        echo "💡 Попробуйте установить вручную: sudo apt-get install nodejs"
    fi
else
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    echo "✅ Node.js установлен: $(node --version)"
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo "⚠️  Требуется Node.js 18+, текущая версия: $(node --version)"
        echo "💡 Обновление Node.js может потребовать ручной установки"
    fi
fi

# Podman
if ! command -v podman &> /dev/null; then
    echo "📦 Установка Podman..."
    # Пробуем установить podman или docker.io (в Astra Linux может быть docker.io)
    if install_package "podman"; then
        # Настройка rootless режима
        echo "⚙️  Настройка rootless режима Podman..."
        podman system migrate 2>/dev/null || echo "⚠️  Не удалось настроить rootless режим (может потребоваться перезагрузка)"
    else
        echo "⚠️  Podman не найден в репозиториях"
        echo "💡 В Astra Linux может использоваться docker.io вместо podman"
        echo "💡 Или установите podman вручную из репозиториев"
    fi
else
    echo "✅ Podman установлен: $(podman --version)"
fi

# Дополнительные зависимости
install_package "git"
install_package "curl"

# 3. Установка зависимостей проекта
echo ""
echo "📦 Установка зависимостей проекта..."

# Backend
echo "Backend зависимости..."
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения Python..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Backend зависимости установлены"

# Frontend
echo "Frontend зависимости..."
cd "$PROJECT_ROOT/frontend/web"
if [ ! -d "node_modules" ]; then
    echo "Установка npm пакетов..."
    npm install --silent
fi
echo "✅ Frontend зависимости установлены"

# 4. Создание образа Astra Linux (опционально)
echo ""
read -p "Создать образ Astra Linux для песочниц? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd "$PROJECT_ROOT/scripts"
    if [ -f "create-astra-image.sh" ]; then
        echo "🔨 Создание образа Astra Linux..."
        echo "⚠️  Примечание: проверка уязвимостей будет отключена для создания образа тренажёра"
        echo "💡 Если создание не удастся, будет использован готовый образ из реестра Astra Linux"
        echo ""
        sudo bash create-astra-image.sh || {
            echo ""
            echo "⚠️  Ошибка создания образа через debootstrap"
            echo "💡 Скрипт должен был попробовать загрузить образ из реестра"
            echo "💡 Образ можно создать позже командой:"
            echo "   cd scripts && sudo ./create-astra-image.sh"
            echo ""
            read -p "Продолжить без образа? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        }
    else
        echo "⚠️  Скрипт create-astra-image.sh не найден"
    fi
fi

# 5. Создание скрипта запуска
echo ""
echo "📝 Создание скрипта запуска..."
LAUNCH_SCRIPT="$PROJECT_ROOT/start-trainer.sh"
cat > "$LAUNCH_SCRIPT" << 'EOF'
#!/bin/bash
# Скрипт запуска Astra Linux Training Simulator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Запуск backend
echo "🚀 Запуск Backend..."
cd backend
source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# Ожидание запуска backend
sleep 3

# Запуск frontend
echo "🌐 Запуск Frontend..."
cd frontend/web
npm start &
FRONTEND_PID=$!
cd ../..

echo ""
echo "✅ Приложение запущено!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Для остановки нажмите Ctrl+C"

# Ожидание сигнала
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
EOF

chmod +x "$LAUNCH_SCRIPT"
echo "✅ Скрипт запуска создан: $LAUNCH_SCRIPT"

# 6. Создание ярлыка на рабочем столе
echo ""
echo "📌 Создание ярлыка на рабочем столе..."
DESKTOP_FILE="$DESKTOP_DIR/astra-trainer.desktop"

# Создаём .desktop файл с правильным путём
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Name[ru]=Тренажёр Astra Linux
Comment=Тренажёр для безопасного обучения работе с Astra Linux
Comment[ru]=Тренажёр для безопасного обучения работе с Astra Linux
Exec=bash "$LAUNCH_SCRIPT"
Icon=application-x-executable
Terminal=true
Categories=Education;Development;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"
echo "✅ Ярлык создан: $DESKTOP_FILE"

# Также создаём в ~/.local/share/applications для меню приложений
APPLICATIONS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPLICATIONS_DIR"
cp "$DESKTOP_FILE" "$APPLICATIONS_DIR/"
echo "✅ Ярлык добавлен в меню приложений"

# 7. Запуск проекта
echo ""
read -p "Запустить проект сейчас? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Запуск проекта..."
    bash "$LAUNCH_SCRIPT"
else
    echo ""
    echo "✅ Установка завершена!"
    echo ""
    echo "Для запуска проекта используйте:"
    echo "  $LAUNCH_SCRIPT"
    echo ""
    echo "Или дважды кликните на ярлык на рабочем столе:"
    echo "  $DESKTOP_FILE"
fi

