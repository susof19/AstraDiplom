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

# Функция для установки Node.js с альтернативными источниками
install_nodejs() {
    local NODE_VERSION="20.x"  # Обновлено до Node.js 20.x LTS
    local sources=(
        "https://deb.nodesource.com/setup_${NODE_VERSION}"
        "https://raw.githubusercontent.com/nodesource/distributions/master/deb/setup_${NODE_VERSION}"
        "https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-x64.tar.xz"
    )
    
    echo "📦 Установка Node.js ${NODE_VERSION}..."
    
    # Проверяем наличие NodeSource репозитория
    if [ ! -f /etc/apt/sources.list.d/nodesource.list ]; then
        echo "🔗 Добавление репозитория NodeSource..."
        local setup_success=false
        
        # Пробуем первый источник (основной)
        echo "   Попытка 1/3: deb.nodesource.com..."
        echo "   ⬇️  Загрузка скрипта установки..."
        if curl --progress-bar --fail --show-error \
            https://deb.nodesource.com/setup_${NODE_VERSION} 2>&1 | \
            sudo -E bash - 2>&1 | grep -v "Смена носителя"; then
            setup_success=true
            echo "   ✅ Репозиторий добавлен успешно"
        else
            echo "   ⚠️  Не удалось загрузить с основного источника"
        fi
        
        # Если не получилось, пробуем альтернативный источник
        if [ "$setup_success" = false ]; then
            echo "   Попытка 2/3: GitHub raw (альтернативный источник)..."
            echo "   ⬇️  Загрузка скрипта установки..."
            if curl --progress-bar --fail --show-error \
                https://raw.githubusercontent.com/nodesource/distributions/master/deb/setup_${NODE_VERSION} 2>&1 | \
                sudo -E bash - 2>&1 | grep -v "Смена носителя"; then
                setup_success=true
                echo "   ✅ Репозиторий добавлен успешно"
            else
                echo "   ⚠️  Не удалось загрузить с альтернативного источника"
            fi
        fi
        
        # Если всё ещё не получилось, пробуем установить из стандартных репозиториев
        if [ "$setup_success" = false ]; then
            echo "   Попытка 3/3: установка из стандартных репозиториев..."
            echo "   ⚠️  NodeSource недоступен, используем стандартные репозитории"
        fi
        
        # Обновляем список пакетов после добавления репозитория
        echo "📋 Обновление списка пакетов..."
        sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null || \
        sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true
    fi
    
    # Устанавливаем Node.js с игнорированием CD
    echo "📥 Установка nodejs из сетевых репозиториев..."
    DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
        -o Acquire::cdrom::AutoDetect=false \
        -o Acquire::cdrom::mount=/dev/null \
        nodejs 2>&1 | grep -v "Смена носителя" || {
        echo "⚠️  Попытка установки без опций CD..."
        DEBIAN_FRONTEND=noninteractive sudo apt-get install -y nodejs
    }
    
    if command -v node &> /dev/null; then
        echo "✅ Node.js установлен: $(node --version)"
        return 0
    else
        echo "❌ Не удалось установить Node.js автоматически"
        echo "💡 Попробуйте установить вручную: sudo apt-get install nodejs"
        return 1
    fi
}

# Node.js 20+
if ! command -v node &> /dev/null; then
    install_nodejs
else
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    echo "✅ Node.js установлен: $(node --version)"
    if [ "$NODE_VERSION" -lt 20 ]; then
        echo "⚠️  Рекомендуется Node.js 20+, текущая версия: $(node --version)"
        read -p "Обновить Node.js до версии 20.x? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Удаляем старый репозиторий если есть
            sudo rm -f /etc/apt/sources.list.d/nodesource.list
            install_nodejs
        fi
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

# PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "📦 Установка PostgreSQL..."
    if install_package "postgresql"; then
        install_package "postgresql-contrib"
        echo "✅ PostgreSQL установлен"
        
        # Запуск PostgreSQL
        echo "⚙️  Запуск PostgreSQL..."
        sudo systemctl start postgresql 2>/dev/null || true
        sudo systemctl enable postgresql 2>/dev/null || true
        
        # Создание базы данных и пользователя
        echo "🔧 Настройка базы данных..."
        DB_SETUP_SCRIPT="/tmp/setup_db.sql"
        cat > "$DB_SETUP_SCRIPT" << 'DBEOF'
-- Создание пользователя (если не существует)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'trainer_user') THEN
        CREATE USER trainer_user WITH PASSWORD 'trainer_password';
    END IF;
END
$$;

-- Создание базы данных (если не существует)
SELECT 'CREATE DATABASE trainer_db OWNER trainer_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trainer_db')\gexec

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE trainer_db TO trainer_user;
DBEOF
        
        sudo -u postgres psql -f "$DB_SETUP_SCRIPT" 2>/dev/null || {
            echo "⚠️  Не удалось автоматически настроить базу данных"
            echo "💡 Выполните вручную:"
            echo "   sudo -u postgres psql"
            echo "   CREATE USER trainer_user WITH PASSWORD 'trainer_password';"
            echo "   CREATE DATABASE trainer_db OWNER trainer_user;"
            echo "   \\q"
        }
        
        rm -f "$DB_SETUP_SCRIPT"
    fi
else
    echo "✅ PostgreSQL установлен: $(psql --version | head -1)"
    
    # Проверяем, запущен ли PostgreSQL
    if ! sudo systemctl is-active --quiet postgresql; then
        echo "⚙️  Запуск PostgreSQL..."
        sudo systemctl start postgresql 2>/dev/null || true
    fi
fi

# Дополнительные зависимости
install_package "git"
install_package "curl"

# 3. Установка зависимостей проекта
echo ""
echo "📦 Установка зависимостей проекта..."

# Backend
echo "Backend зависимости..."
echo "   Текущая директория: $(pwd)"
echo "   Переход в: $PROJECT_ROOT/backend"
if [ ! -d "$PROJECT_ROOT/backend" ]; then
    echo "❌ Ошибка: директория backend не найдена"
    echo "💡 Проверьте путь: $PROJECT_ROOT/backend"
    echo "💡 Текущий PROJECT_ROOT: $PROJECT_ROOT"
    exit 1
fi

cd "$PROJECT_ROOT/backend" || {
    echo "❌ Ошибка: не удалось перейти в директорию backend"
    echo "💡 Проверьте путь: $PROJECT_ROOT/backend"
    exit 1
}
echo "   ✅ Переход выполнен, текущая директория: $(pwd)"

if [ ! -d "venv" ]; then
    echo "   Создание виртуального окружения Python..."
    if ! python3 -m venv venv; then
        echo "❌ Ошибка создания виртуального окружения"
        echo "💡 Проверьте установку python3-venv: sudo apt-get install python3-venv"
        exit 1
    fi
    echo "   ✅ Виртуальное окружение создано"
fi

# Проверяем существование файла активации перед попыткой активации
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Ошибка: файл активации виртуального окружения не найден"
    echo "💡 Попробуйте удалить venv и пересоздать: rm -rf venv && python3 -m venv venv"
    exit 1
fi

echo "   Активация виртуального окружения..."
source venv/bin/activate || {
    echo "❌ Ошибка активации виртуального окружения"
    exit 1
}

echo "   Обновление pip..."
if ! pip install --upgrade pip 2>&1 | tee /tmp/pip-upgrade.log | \
    grep -E "(Collecting|Installing|Requirement|Successfully|Downloading|Upgrading)" || true; then
    # Если команда не выполнилась, проверяем лог
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo "   ⚠️  Возможна проблема при обновлении pip"
        tail -10 /tmp/pip-upgrade.log 2>/dev/null || true
    fi
fi

# Проверяем наличие requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "❌ Ошибка: файл requirements.txt не найден в $PROJECT_ROOT/backend"
    echo "💡 Убедитесь, что файл существует"
    exit 1
fi

echo "   Установка зависимостей из requirements.txt..."
echo "   ⬇️  Загрузка пакетов..."
pip install -r requirements.txt 2>&1 | tee /tmp/pip-install.log | \
    grep -E "(Collecting|Installing|Requirement|Successfully|Downloading|Building)" || true

# Проверяем успешность установки по коду возврата pip
PIP_EXIT_CODE=${PIPESTATUS[0]}
if [ $PIP_EXIT_CODE -eq 0 ]; then
echo "✅ Backend зависимости установлены"
else
    echo "⚠️  Возможны проблемы с установкой зависимостей (код возврата: $PIP_EXIT_CODE)"
    echo "💡 Показываем последние строки лога:"
    tail -30 /tmp/pip-install.log 2>/dev/null || true
    echo "💡 Попробуйте установить вручную: cd backend && source venv/bin/activate && pip install -r requirements.txt"
fi

# Инициализация базы данных
echo "   Инициализация базы данных PostgreSQL..."
if python init_db.py 2>&1; then
    echo "✅ База данных инициализирована"
else
    echo "⚠️  Не удалось инициализировать базу данных"
    echo "💡 Убедитесь, что PostgreSQL запущен и база данных создана"
    echo "💡 Выполните вручную: python init_db.py"
fi

# Frontend
echo "Frontend зависимости..."
cd "$PROJECT_ROOT/frontend/web"
if [ ! -d "node_modules" ]; then
    echo "   Установка npm пакетов (это может занять некоторое время)..."
    echo "   ⬇️  Загрузка пакетов..."
    # npm install показывает прогресс по умолчанию, используем стандартный вывод
    npm install 2>&1 | tee /tmp/npm-install.log | \
        grep -E "(added|removed|changed|audited|npm WARN|npm ERR|Downloading|Installing|Building)" || {
        # Если grep ничего не нашёл или произошла ошибка, показываем последние строки
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            echo "   ⚠️  Произошла ошибка, показываем последние строки лога:"
            tail -20 /tmp/npm-install.log 2>/dev/null || true
        fi
    }
    # Проверяем успешность установки
    if [ -d "node_modules" ] && [ -f "package-lock.json" ]; then
        echo "   ✅ Пакеты установлены успешно"
    else
        echo "   ⚠️  Возможна проблема с установкой, проверьте лог выше"
    fi
else
    echo "   ✅ node_modules уже существует, пропускаем установку"
fi
echo "✅ Frontend зависимости установлены"

# 4. Создание образов Astra Linux
echo ""
echo "🔨 Создание образов Astra Linux..."
echo ""
echo "Доступные варианты:"
echo "  1) Базовый образ (для CLI-миссий: уровни B, C)"
echo "  2) Образ с VNC (для GUI-миссий: уровень A)"
echo "  3) Оба образа"
echo "  4) Пропустить (создать позже)"
echo ""
read -p "Выберите вариант (1-4): " -n 1 -r
echo
echo ""

cd "$PROJECT_ROOT/scripts"

case $REPLY in
    1)
        echo "📦 Создание базового образа..."
        bash create-astra-image.sh || {
            echo "⚠️  Ошибка создания образа"
            echo "💡 Образ можно создать позже: cd scripts && ./create-astra-image.sh"
        }
        ;;
    2)
        echo "📦 Создание образа с VNC..."
        bash create-astra-image.sh --vnc || {
            echo "⚠️  Ошибка создания образа"
            echo "💡 Образ можно создать позже: cd scripts && ./create-astra-image.sh --vnc"
        }
        ;;
    3)
        echo "📦 Создание базового образа..."
        bash create-astra-image.sh || echo "⚠️  Ошибка создания базового образа"
        echo ""
        echo "📦 Создание образа с VNC..."
        bash create-astra-image.sh --vnc || echo "⚠️  Ошибка создания образа с VNC"
        ;;
    4)
        echo "⏭️  Пропуск создания образов"
        echo "💡 Образы можно создать позже командами:"
        echo "   cd scripts"
        echo "   ./create-astra-image.sh          # Базовый"
        echo "   ./create-astra-image.sh --vnc    # С VNC"
        ;;
    *)
        echo "❌ Неверный выбор, пропускаем создание образов"
        ;;
esac

cd "$PROJECT_ROOT"

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

