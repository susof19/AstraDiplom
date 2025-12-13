#!/bin/bash
# Скрипт быстрого старта для WSL (Windows Subsystem for Linux)
# Адаптирован для работы в WSL с учетом особенностей Windows

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Определение пути к рабочему столу Windows (если доступен)
if [ -d "/mnt/c/Users/$USER/Desktop" ]; then
    DESKTOP_DIR="/mnt/c/Users/$USER/Desktop"
elif [ -d "/mnt/c/Users/$USER/Рабочий стол" ]; then
    DESKTOP_DIR="/mnt/c/Users/$USER/Рабочий стол"
else
    DESKTOP_DIR="$HOME"
fi

APP_NAME="Linux Training Simulator"

echo "🚀 Установка Linux Training Simulator для WSL"
echo "=================================================="
echo ""

# Проверка WSL
if [ -f /proc/version ] && grep -qi microsoft /proc/version; then
    echo "✅ Обнаружен WSL"
    WSL_VERSION=$(uname -r | grep -oP 'microsoft-standard-WSL\K\d+' || echo "2")
    echo "   Версия WSL: $WSL_VERSION"
else
    echo "⚠️  Не похоже на WSL, но продолжаем..."
fi
echo ""

# Функция проверки доступности sudo
check_sudo() {
    if ! command -v sudo &> /dev/null; then
        return 1
    fi
    if sudo -n true 2>/dev/null; then
        return 0
    fi
    local sudo_output
    sudo_output=$(sudo -v 2>&1)
    local sudo_exit=$?
    if [ $sudo_exit -ne 0 ]; then
        return 1
    fi
    return 0
}

# Проверка прав root
HAS_SUDO=false
if [ "$EUID" -ne 0 ]; then 
    echo "🔍 Проверка прав администратора..."
    if check_sudo; then
        HAS_SUDO=true
        echo "✅ Права sudo доступны"
    else
        echo "⚠️  Нет прав sudo, некоторые операции могут быть пропущены"
    fi
else
    HAS_SUDO=true
    echo "✅ Запущено от имени root"
fi
echo ""

# Функция для установки пакетов
install_package() {
    local package=$1
    
    if [ "$HAS_SUDO" != true ]; then
        echo "⚠️  Пропуск установки $package (нет прав sudo)"
        return 1
    fi
    
    if ! dpkg -l 2>/dev/null | grep -q "^ii.*$package"; then
        echo "📦 Установка $package..."
        sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true
        if DEBIAN_FRONTEND=noninteractive sudo apt-get install -y "$package" 2>&1; then
            echo "✅ $package установлен"
        else
            echo "❌ Ошибка установки $package"
            return 1
        fi
    else
        echo "✅ $package уже установлен"
    fi
}

# 1. Обновление списка пакетов
if [ "$HAS_SUDO" = true ]; then
    echo "📋 Обновление списка пакетов..."
    sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true
fi

# 2. Установка системных зависимостей
echo ""
echo "🔧 Установка системных зависимостей..."

# curl и wget
if ! command -v curl &> /dev/null; then
    install_package "curl"
fi
if ! command -v wget &> /dev/null; then
    install_package "wget"
fi

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
    
    if [ "$HAS_SUDO" = true ]; then
        # Используем NodeSource для установки Node.js 20.x LTS
        echo "   ⬇️  Загрузка скрипта установки NodeSource..."
        
        if command -v curl &> /dev/null; then
            curl --progress-bar --fail https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>&1 || {
                echo "   ⚠️  Не удалось загрузить с основного источника, пробуем альтернативный..."
                curl --progress-bar --fail https://raw.githubusercontent.com/nodesource/distributions/master/deb/setup_20.x | sudo -E bash - 2>&1 || {
                    echo "   ⚠️  Не удалось добавить репозиторий NodeSource"
                    install_package "nodejs"
                }
            }
        fi
        
        sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true
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

# PostgreSQL - специальная обработка для WSL
echo ""
echo "📦 Установка PostgreSQL..."
if ! command -v psql &> /dev/null; then
    if install_package "postgresql"; then
        install_package "postgresql-contrib"
        echo "✅ PostgreSQL установлен"
    fi
else
    echo "✅ PostgreSQL установлен: $(psql --version | head -1)"
fi

# Запуск PostgreSQL в WSL (используем service вместо systemctl)
if [ "$HAS_SUDO" = true ]; then
    echo "⚙️  Настройка PostgreSQL для WSL..."
    
    # В WSL systemctl может не работать, используем service
    if command -v service &> /dev/null; then
        echo "   Запуск PostgreSQL через service..."
        sudo service postgresql start 2>/dev/null || {
            echo "   ⚠️  Не удалось запустить через service, пробуем вручную..."
            sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/*/main start 2>/dev/null || true
        }
    else
        echo "   ⚠️  service не найден, запускаем вручную..."
        sudo -u postgres /usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/*/main start 2>/dev/null || true
    fi
    
    # Создание пользователя и базы данных
    echo "🔧 Настройка базы данных..."
    sleep 2  # Даем PostgreSQL время на запуск
    
    # Создаем скрипт для настройки БД
    DB_SETUP_SCRIPT="/tmp/setup_db_wsl.sql"
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
    
    # Выполняем скрипт
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

# Docker Desktop для WSL (рекомендуется)
echo ""
echo "🐳 Проверка Docker/Podman..."
if ! command -v docker &> /dev/null && ! command -v podman &> /dev/null; then
    echo "⚠️  Docker или Podman не найдены"
    echo "💡 Для WSL рекомендуется использовать Docker Desktop для Windows"
    echo "   Скачайте: https://www.docker.com/products/docker-desktop"
    echo "   После установки Docker Desktop, Docker будет доступен в WSL"
    echo ""
    read -p "Продолжить без Docker/Podman? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Установка прервана"
        exit 1
    fi
else
    if command -v docker &> /dev/null; then
        echo "✅ Docker установлен: $(docker --version)"
        # Проверяем, работает ли Docker
        if docker info &>/dev/null; then
            echo "✅ Docker работает"
        else
            echo "⚠️  Docker установлен, но не работает"
            echo "💡 Убедитесь, что Docker Desktop запущен в Windows"
        fi
    elif command -v podman &> /dev/null; then
        echo "✅ Podman установлен: $(podman --version)"
    fi
fi

# Дополнительные зависимости
install_package "git"
install_package "build-essential"
if [ "$HAS_SUDO" = true ]; then
    install_package "python3-dev"
    install_package "libffi-dev"
    install_package "libssl-dev"
fi

# 3. Настройка Backend
echo ""
echo "🐍 Настройка Python Backend..."

cd "$PROJECT_ROOT/backend" || {
    echo "❌ Ошибка: не удалось перейти в директорию backend"
    exit 1
}

# Создаем venv если его нет или если он поврежден
if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
    if [ -d "venv" ]; then
        echo "   ⚠️  Виртуальное окружение повреждено, пересоздаем..."
        rm -rf venv
    fi
    echo "   📦 Создание виртуального окружения Python..."
    if ! python3 -m venv venv; then
        echo "❌ Ошибка создания виртуального окружения"
        echo "💡 Проверьте установку python3-venv:"
        if [ "$HAS_SUDO" = true ]; then
            echo "   sudo apt-get install python3-venv"
        else
            echo "   Попросите администратора установить: python3-venv"
        fi
        exit 1
    fi
    echo "   ✅ Виртуальное окружение создано"
else
    echo "   ✅ Виртуальное окружение уже существует"
fi

# Проверяем наличие activate (дополнительная проверка)
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Ошибка: файл активации не найден после создания"
    echo "💡 Попробуйте удалить venv и пересоздать:"
    echo "   rm -rf venv && python3 -m venv venv"
    exit 1
fi

# Проверяем requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "❌ Ошибка: requirements.txt не найден"
    exit 1
fi

echo "   Активация виртуального окружения..."
source venv/bin/activate || {
    echo "❌ Ошибка активации виртуального окружения"
    exit 1
}

echo "   📦 Установка Python зависимостей..."
pip install --upgrade pip setuptools wheel 2>&1 | grep -E "(Collecting|Installing|Requirement|Successfully)" || true
pip install -r requirements.txt 2>&1 | grep -E "(Collecting|Installing|Requirement|Successfully|ERROR)" || true

# Инициализация базы данных
echo "   Инициализация базы данных PostgreSQL..."
if python init_db.py 2>&1; then
    echo "✅ База данных инициализирована"
else
    echo "⚠️  Не удалось инициализировать базу данных"
    echo "💡 Убедитесь, что PostgreSQL запущен"
fi

deactivate
echo "✅ Backend настроен"

# 4. Настройка Frontend
echo ""
echo "🌐 Настройка React Frontend..."

cd "$PROJECT_ROOT/frontend/web" || {
    echo "❌ Ошибка: не удалось перейти в директорию frontend/web"
    exit 1
}

if [ ! -f "package.json" ]; then
    echo "❌ Ошибка: package.json не найден"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "   📦 Установка Node.js зависимостей..."
    npm install 2>&1 | grep -E "(added|removed|changed|audited|npm WARN|npm ERR)" || true
else
    echo "   📦 Обновление Node.js зависимостей..."
    npm install 2>&1 | grep -E "(added|removed|changed|audited|npm WARN|npm ERR)" || true
fi

echo "✅ Frontend настроен"

# 5. Создание скрипта запуска для WSL
echo ""
echo "📝 Создание скрипта запуска для WSL..."
cd "$PROJECT_ROOT"

cat > start-demo-wsl.sh << 'EOF'
#!/bin/bash
# Скрипт запуска Linux Training Simulator для WSL

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

echo "🚀 Запуск Linux Training Simulator (WSL)"
echo "=================================================="
echo ""

# Проверка и запуск PostgreSQL
echo "⚙️  Проверка PostgreSQL..."
if ! pg_isready -h localhost -U postgres &>/dev/null; then
    echo "   Запуск PostgreSQL..."
    if command -v service &> /dev/null; then
        sudo service postgresql start 2>/dev/null || {
            echo "⚠️  Не удалось запустить PostgreSQL через service"
            echo "💡 Попробуйте вручную: sudo service postgresql start"
        }
    else
        echo "⚠️  service не найден, запустите PostgreSQL вручную"
    fi
    sleep 2
else
    echo "✅ PostgreSQL запущен"
fi
echo ""

# Запуск Backend
echo "🚀 Запуск Backend..."
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "💡 Запустите: ./scripts/quickstart-wsl.sh"
    exit 1
fi

source venv/bin/activate
nohup python run.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend запущен (PID: $BACKEND_PID)"
cd "$PROJECT_ROOT"

# Ожидание запуска Backend
echo "⏳ Ожидание запуска Backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend готов"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend не отвечает, проверьте логи: tail -f backend.log"
    fi
    sleep 1
done
echo ""

# Запуск Frontend
echo "🌐 Запуск Frontend..."
cd "$PROJECT_ROOT/frontend/web"
BROWSER=none nohup npm start > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend запущен (PID: $FRONTEND_PID)"
cd "$PROJECT_ROOT"

# Ожидание запуска Frontend
echo "⏳ Ожидание запуска Frontend..."
sleep 5

echo ""
echo "=================================================="
echo "✅ Демонстрация запущена!"
echo ""
echo "📋 Сервисы:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Логи:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 Для остановки:"
echo "   ./stop-demo.sh"
echo "   или"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "=================================================="

# Сохранение PID для остановки
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid
EOF

chmod +x start-demo-wsl.sh
echo "✅ Скрипт start-demo-wsl.sh создан"

echo ""
echo "=================================================="
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Запустите приложение:"
echo "      ./start-demo-wsl.sh"
echo ""
echo "   2. Откройте в браузере Windows:"
echo "      http://localhost:3000"
echo ""
echo "💡 Примечания для WSL:"
echo "   - PostgreSQL запускается автоматически при старте"
echo "   - Docker Desktop должен быть запущен в Windows"
echo "   - Frontend будет доступен на localhost:3000 в Windows"
echo "=================================================="

