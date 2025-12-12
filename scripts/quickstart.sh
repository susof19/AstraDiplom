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

# Функция проверки доступности sudo
check_sudo() {
    if ! command -v sudo &> /dev/null; then
        return 1
    fi
    
    # Проверяем, может ли пользователь выполнять sudo команды без пароля
    if sudo -n true 2>/dev/null; then
        return 0
    fi
    
    # Пробуем выполнить sudo -v и проверяем вывод на ошибки
    local sudo_output
    sudo_output=$(sudo -v 2>&1)
    local sudo_exit=$?
    
    # Если команда вернула ошибку, проверяем причину
    if [ $sudo_exit -ne 0 ]; then
        # Проверяем, есть ли в выводе сообщение об отсутствии в sudoers
        if echo "$sudo_output" | grep -qiE "отсутствует в файле sudoers|not in the sudoers file|is not in the sudoers file"; then
            return 1
        fi
        # Другие ошибки тоже означают проблему
        return 1
    fi
    
    # Если sudo -v выполнился успешно, права есть
    return 0
}

# Проверка прав root для установки пакетов
HAS_SUDO=false
if [ "$EUID" -ne 0 ]; then 
    echo "🔍 Проверка прав администратора..."
    if check_sudo; then
        HAS_SUDO=true
        echo "✅ Права sudo доступны"
    else
        echo ""
        echo "❌ ПРОБЛЕМА: Пользователь '$USER' не имеет прав sudo"
        echo ""
        echo "⚠️  ВНИМАНИЕ: Для установки системных пакетов требуются права администратора"
        echo ""
        echo "💡 Решения:"
        echo ""
        echo "   Вариант 1: Попросите администратора добавить вас в группу sudo"
        echo "   ──────────────────────────────────────────────────────────────"
        echo "   Администратор должен выполнить:"
        echo "   su -c \"usermod -aG sudo $USER\""
        echo "   (После этого нужно выйти и войти снова)"
        echo ""
        echo "   Вариант 2: Добавить в /etc/sudoers (требует root)"
        echo "   ──────────────────────────────────────────────────────────────"
        echo "   su -c \"echo '$USER ALL=(ALL:ALL) ALL' >> /etc/sudoers\""
        echo ""
        echo "   Вариант 3: Запустить скрипт от имени root"
        echo "   ──────────────────────────────────────────────────────────────"
        echo "   su -c \"bash $(realpath "$0")\""
        echo ""
        echo "   Вариант 4: Продолжить без установки системных пакетов"
        echo "   ──────────────────────────────────────────────────────────────"
        echo "   Скрипт установит только пользовательские зависимости:"
        echo "   - Python пакеты в venv (не требует sudo)"
        echo "   - npm пакеты локально (не требует sudo)"
        echo "   Но вам нужно будет вручную установить:"
        echo "   - python3, python3-venv, nodejs, npm"
        echo ""
        read -p "Продолжить без установки системных пакетов? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "❌ Установка прервана пользователем"
            echo "💡 Выберите один из вариантов выше для получения прав sudo"
            exit 1
        fi
        echo ""
        echo "⚠️  Продолжаем БЕЗ установки системных пакетов..."
        echo "   Убедитесь, что установлены: python3, python3-venv, nodejs, npm"
        echo ""
    fi
else
    HAS_SUDO=true
    echo "✅ Запущено от имени root"
    echo ""
fi

# Отключение CD-репозитория если он мешает (актуально для некоторых дистрибутивов)
if [ "$HAS_SUDO" = true ]; then
    if grep -q "^deb cdrom:" /etc/apt/sources.list 2>/dev/null || \
       find /etc/apt/sources.list.d -name "*.list" -exec grep -q "^deb cdrom:" {} \; 2>/dev/null; then
        echo "🔧 Обнаружен CD-репозиторий, настраиваем использование только сетевых репозиториев..."
        if [ ! -f /etc/apt/apt.conf.d/99no-cdrom ]; then
            if echo 'Acquire::cdrom::AutoDetect "false";' | sudo tee /etc/apt/apt.conf.d/99no-cdrom > /dev/null 2>&1 && \
               echo 'Acquire::cdrom::mount "/dev/null";' | sudo tee -a /etc/apt/apt.conf.d/99no-cdrom > /dev/null 2>&1; then
                echo "✅ CD-репозиторий отключен для этой установки"
            else
                echo "⚠️  Не удалось отключить CD-репозиторий (требуются права sudo)"
            fi
        fi
    fi
fi

# Функция для установки пакетов
install_package() {
    local package=$1
    
    if [ "$HAS_SUDO" != true ]; then
        echo "⚠️  Пропуск установки $package (нет прав sudo)"
        echo "💡 Установите вручную: sudo apt-get install $package"
        return 1
    fi
    
    if ! dpkg -l 2>/dev/null | grep -q "^ii.*$package"; then
        echo "📦 Установка $package..."
        
        # Обновляем список пакетов без CD-репозитория
        if ! sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null; then
            sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true
        fi
        
        # Пытаемся установить из сетевых репозиториев
        if ! DEBIAN_FRONTEND=noninteractive sudo apt-get install -y \
            -o Acquire::cdrom::AutoDetect=false \
            -o Acquire::cdrom::mount=/dev/null \
            --no-install-recommends \
            "$package" 2>&1 | grep -v "Смена носителя"; then
            echo "⚠️  Повторная попытка установки $package..."
            if ! DEBIAN_FRONTEND=noninteractive sudo apt-get install -y "$package" 2>&1; then
                echo "❌ Ошибка установки $package"
                echo "💡 Попробуйте установить вручную: sudo apt-get install $package"
                return 1
            fi
        fi
        echo "✅ $package установлен"
    else
        echo "✅ $package уже установлен"
    fi
}

# 1. Обновление списка пакетов
if [ "$HAS_SUDO" = true ]; then
    echo "📋 Обновление списка пакетов..."
    if ! sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null; then
        sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true
    fi
else
    echo "⚠️  Пропуск обновления списка пакетов (нет прав sudo)"
fi

# 2. Установка системных зависимостей
echo ""
echo "🔧 Установка системных зависимостей..."

# Сначала устанавливаем curl и wget (нужны для загрузки скриптов)
if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
    echo "📦 Установка curl/wget (необходимы для загрузки файлов)..."
    install_package "curl"
    install_package "wget"
elif ! command -v curl &> /dev/null; then
    install_package "curl"
elif ! command -v wget &> /dev/null; then
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

# Функция для загрузки файла с альтернативными методами
download_file() {
    local url=$1
    if command -v curl &> /dev/null; then
        curl --progress-bar --fail --show-error "$url" 2>&1
        return $?
    elif command -v wget &> /dev/null; then
        wget --progress=bar:force -qO- "$url" 2>&1
        return $?
    else
        echo "❌ Ошибка: curl и wget не найдены" >&2
        return 1
    fi
}

# Node.js 18+
if ! command -v node &> /dev/null; then
    echo "📦 Установка Node.js..."
    
    if [ "$HAS_SUDO" = true ]; then
        # Для разных дистрибутивов разные способы установки Node.js
        if [ "$DISTRO_ID" = "ubuntu" ] || [ "$DISTRO_ID" = "debian" ]; then
            # Используем NodeSource для Ubuntu/Debian
            echo "   ⬇️  Загрузка скрипта установки NodeSource..."
            
            # Проверяем наличие curl или wget
            if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
                echo "❌ Ошибка: curl и wget не найдены"
                echo "💡 Установите curl: sudo apt-get install curl"
                echo "⚠️  Пробуем установить Node.js из стандартных репозиториев..."
                install_package "nodejs"
            else
                # Пробуем загрузить скрипт установки NodeSource
                local setup_success=false
                
                # Пробуем основной источник
                echo "   Попытка 1/2: deb.nodesource.com..."
                if download_file https://deb.nodesource.com/setup_18.x 2>/dev/null | sudo -E bash - 2>&1; then
                    setup_success=true
                    echo "   ✅ Репозиторий NodeSource добавлен"
                else
                    echo "   ⚠️  Не удалось загрузить с основного источника"
                fi
                
                # Если не получилось, пробуем альтернативный источник
                if [ "$setup_success" = false ]; then
                    echo "   Попытка 2/2: GitHub raw (альтернативный источник)..."
                    if download_file https://raw.githubusercontent.com/nodesource/distributions/master/deb/setup_18.x 2>/dev/null | sudo -E bash - 2>&1; then
                        setup_success=true
                        echo "   ✅ Репозиторий NodeSource добавлен (альтернативный источник)"
                    else
                        echo "   ⚠️  Не удалось добавить репозиторий NodeSource"
                        echo "   💡 Пробуем установить Node.js из стандартных репозиториев..."
                    fi
                fi
                
                # Обновляем список пакетов после добавления репозитория
                if [ "$setup_success" = true ]; then
                    echo "   📋 Обновление списка пакетов..."
                    sudo apt-get update -qq -o Acquire::cdrom::AutoDetect=false 2>/dev/null || \
                    sudo apt-get update -qq 2>&1 | grep -v "Смена носителя" || true
                fi
                
                # Устанавливаем nodejs
                install_package "nodejs"
            fi
        else
            # Для других дистрибутивов пробуем стандартный способ
            install_package "nodejs"
        fi
        
        if ! command -v node &> /dev/null || [ "$(node --version | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
            echo "⚠️  Node.js не установлен или версия < 18"
            echo "💡 Установите Node.js 18+ вручную: https://nodejs.org/"
        fi
    else
        echo "⚠️  Не удалось установить Node.js (нет прав sudo)"
        echo "💡 Установите Node.js 18+ вручную:"
        echo "   1. Через nvm (не требует sudo): https://github.com/nvm-sh/nvm"
        echo "   2. Или попросите администратора: sudo apt-get install nodejs"
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

# PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "📦 Установка PostgreSQL..."
    if install_package "postgresql"; then
        install_package "postgresql-contrib"
        echo "✅ PostgreSQL установлен"
        
        # Проверяем, запущен ли PostgreSQL
        if [ "$HAS_SUDO" = true ]; then
            echo "⚙️  Запуск PostgreSQL..."
            sudo systemctl start postgresql 2>/dev/null || true
            sudo systemctl enable postgresql 2>/dev/null || true
            
            # Создание базы данных и пользователя
            echo "🔧 Настройка базы данных..."
            echo "   Создание базы данных и пользователя..."
            
            # Создаем скрипт для настройки БД
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
            
            # Выполняем скрипт от имени postgres
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
        echo "⚠️  Не удалось установить PostgreSQL (нет прав sudo)"
        echo "💡 Установите вручную: sudo apt-get install postgresql postgresql-contrib"
    fi
else
    echo "✅ PostgreSQL установлен: $(psql --version | head -1)"
    
    # Проверяем, запущен ли PostgreSQL
    if [ "$HAS_SUDO" = true ]; then
        if ! sudo systemctl is-active --quiet postgresql; then
            echo "⚙️  Запуск PostgreSQL..."
            sudo systemctl start postgresql 2>/dev/null || true
        fi
    fi
fi

# Podman или Docker
if ! command -v podman &> /dev/null && ! command -v docker &> /dev/null; then
    echo "📦 Установка Podman..."
    # Пробуем установить podman
    if install_package "podman"; then
        echo "✅ Podman установлен"
        
        # Устанавливаем зависимости для rootless Podman
        if [ "$HAS_SUDO" = true ]; then
            echo "🔧 Установка зависимостей для rootless Podman..."
            install_package "uidmap"      # Содержит newuidmap, newgidmap
            install_package "slirp4netns" # Для сетевых пространств имен
            install_package "fuse-overlayfs" # Для overlay файловой системы
            
            # Настройка rootless режима
            echo "⚙️  Настройка rootless режима Podman..."
            podman system migrate 2>/dev/null || echo "⚠️  Не удалось настроить rootless режим (может потребоваться перезагрузка или выход/вход)"
        fi
    else
        # Если podman недоступен, пробуем docker
        echo "⚠️  Podman недоступен, пробуем Docker..."
        if install_package "docker.io"; then
            echo "✅ Docker установлен (будет использоваться вместо Podman)"
            # Добавляем пользователя в группу docker
            if [ "$HAS_SUDO" = true ]; then
                sudo usermod -aG docker "$USER" 2>/dev/null || true
                echo "⚠️  ВНИМАНИЕ: Для применения изменений группы docker нужно выйти и войти снова"
            fi
        else
            echo "❌ Не удалось установить ни Podman, ни Docker"
            echo "💡 Установите вручную:"
            echo "   sudo apt-get install podman uidmap slirp4netns fuse-overlayfs"
            echo "   или"
            echo "   sudo apt-get install docker.io"
        fi
    fi
else
    if command -v podman &> /dev/null; then
        echo "✅ Podman установлен: $(podman --version)"
        
        # Проверяем наличие зависимостей для rootless Podman
        if [ "$HAS_SUDO" = true ]; then
            MISSING_DEPS=""
            if ! command -v newuidmap &> /dev/null; then
                MISSING_DEPS="$MISSING_DEPS uidmap"
            fi
            if ! command -v slirp4netns &> /dev/null; then
                MISSING_DEPS="$MISSING_DEPS slirp4netns"
            fi
            if ! command -v fuse-overlayfs &> /dev/null; then
                MISSING_DEPS="$MISSING_DEPS fuse-overlayfs"
            fi
            
            if [ -n "$MISSING_DEPS" ]; then
                echo "🔧 Установка недостающих зависимостей для rootless Podman..."
                for dep in $MISSING_DEPS; do
                    install_package "$dep"
                done
            fi
            
            # Настройка rootless режима
            echo "⚙️  Проверка rootless режима Podman..."
            if podman info 2>&1 | grep -q "rootless"; then
                echo "✅ Rootless режим настроен"
            else
                echo "⚠️  Rootless режим может быть не настроен"
                echo "💡 Попробуйте: podman system migrate"
                echo "💡 Или выйдите и войдите снова"
            fi
        fi
    else
        echo "✅ Docker установлен: $(docker --version)"
        # Добавляем пользователя в группу docker
        if [ "$HAS_SUDO" = true ]; then
            sudo usermod -aG docker "$USER" 2>/dev/null || true
            echo "⚠️  ВНИМАНИЕ: Для применения изменений группы docker нужно выйти и войти снова"
        fi
    fi
fi

# Дополнительные зависимости (curl и wget уже установлены выше, если нужны)
if ! command -v curl &> /dev/null; then
    install_package "curl"
fi
if ! command -v wget &> /dev/null; then
    install_package "wget"
fi
install_package "git"
install_package "build-essential"

# Установка инструментов для сборки нативных расширений Python (pydantic-core и др.)
# Это необходимо для сборки Rust-зависимостей, если нет предкомпилированных wheels
if [ "$HAS_SUDO" = true ]; then
    echo "🔧 Установка инструментов для сборки нативных расширений..."
    install_package "python3-dev"
    install_package "libffi-dev"
    install_package "libssl-dev"
    # Rust не обязателен, так как pip может установить предкомпилированные wheels
    # Но если нужна сборка из исходников, можно установить rustc
    # install_package "rustc" || echo "⚠️  Rust не установлен (pip попробует использовать wheels)"
fi

# 3. Настройка Backend
echo ""
echo "🐍 Настройка Python Backend..."
echo "   Переход в: $PROJECT_ROOT/backend"

# Проверяем существование директории backend
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

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
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

# Проверяем существование файла активации перед попыткой активации
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Ошибка: файл активации виртуального окружения не найден"
    echo "💡 Попробуйте удалить venv и пересоздать:"
    echo "   rm -rf venv && python3 -m venv venv"
    exit 1
fi

# Проверяем наличие requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "❌ Ошибка: файл requirements.txt не найден в $PROJECT_ROOT/backend"
    echo "💡 Убедитесь, что файл существует"
    exit 1
fi

echo "   Активация виртуального окружения..."
source venv/bin/activate || {
    echo "❌ Ошибка активации виртуального окружения"
    exit 1
}

echo "   📦 Установка Python зависимостей..."
echo "   Обновление pip..."
if ! pip install --upgrade pip 2>&1 | tee /tmp/pip-upgrade.log | \
    grep -E "(Collecting|Installing|Requirement|Successfully|Downloading|Upgrading)" || true; then
    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        echo "   ⚠️  Возможна проблема при обновлении pip"
        tail -10 /tmp/pip-upgrade.log 2>/dev/null || true
    fi
fi

echo "   Установка зависимостей из requirements.txt..."
echo "   ⬇️  Загрузка пакетов..."

# Обновляем pip, setuptools и wheel для лучшей поддержки wheels
pip install --upgrade pip setuptools wheel 2>&1 | grep -E "(Collecting|Installing|Requirement|Successfully|Downloading|Upgrading)" || true

# Устанавливаем зависимости (pip автоматически попробует использовать wheels, если доступны)
echo "   Установка пакетов (pip попробует использовать предкомпилированные wheels)..."
pip install -r requirements.txt 2>&1 | tee /tmp/pip-install.log | \
    grep -E "(Collecting|Installing|Requirement|Successfully|Downloading|Building|WARNING|ERROR|Failed)" || true

PIP_EXIT_CODE=${PIPESTATUS[0]}

# Проверяем успешность установки
if [ $PIP_EXIT_CODE -eq 0 ]; then
    echo "✅ Backend зависимости установлены"
else
    echo "⚠️  Возможны проблемы с установкой зависимостей (код возврата: $PIP_EXIT_CODE)"
    echo "💡 Показываем последние строки лога:"
    tail -40 /tmp/pip-install.log 2>/dev/null || true
    
    # Проверяем, есть ли ошибки с pydantic-core
    if grep -q "pydantic-core" /tmp/pip-install.log 2>/dev/null; then
        echo ""
        echo "💡 Проблема с pydantic-core (требует Rust для сборки):"
        echo "   Вариант 1: Установите Rust: sudo apt-get install rustc cargo"
        echo "   Вариант 2: Используйте предкомпилированные wheels (pip попробует автоматически)"
        echo "   Вариант 3: Обновите pip: pip install --upgrade pip setuptools wheel"
    fi
    
    echo ""
    echo "💡 Попробуйте установить вручную:"
    echo "   cd backend && source venv/bin/activate && pip install -r requirements.txt"
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

deactivate
echo "✅ Backend настроен"

# 4. Настройка Frontend
echo ""
echo "🌐 Настройка React Frontend..."
echo "   Переход в: $PROJECT_ROOT/frontend/web"

# Проверяем существование директории frontend/web
if [ ! -d "$PROJECT_ROOT/frontend/web" ]; then
    echo "❌ Ошибка: директория frontend/web не найдена"
    echo "💡 Проверьте путь: $PROJECT_ROOT/frontend/web"
    exit 1
fi

cd "$PROJECT_ROOT/frontend/web" || {
    echo "❌ Ошибка: не удалось перейти в директорию frontend/web"
    exit 1
}
echo "   ✅ Переход выполнен, текущая директория: $(pwd)"

# Проверяем наличие package.json
if [ ! -f "package.json" ]; then
    echo "❌ Ошибка: файл package.json не найден"
    echo "💡 Убедитесь, что файл существует"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "   📦 Установка Node.js зависимостей (это может занять некоторое время)..."
    echo "   ⬇️  Загрузка пакетов..."
    npm install 2>&1 | tee /tmp/npm-install.log | \
        grep -E "(added|removed|changed|audited|npm WARN|npm ERR|Downloading|Installing|Building)" || {
        # Если grep ничего не нашёл или произошла ошибка
        if [ ${PIPESTATUS[0]} -ne 0 ]; then
            echo "   ⚠️  Произошла ошибка, показываем последние строки лога:"
            tail -30 /tmp/npm-install.log 2>/dev/null || true
        fi
    }
    
    # Проверяем успешность установки
    NPM_EXIT_CODE=${PIPESTATUS[0]}
    if [ $NPM_EXIT_CODE -eq 0 ] && [ -d "node_modules" ]; then
        echo "   ✅ Пакеты установлены успешно"
    else
        echo "   ⚠️  Возможна проблема с установкой пакетов (код возврата: $NPM_EXIT_CODE)"
        echo "   💡 Попробуйте установить вручную:"
        echo "      cd frontend/web && npm install"
    fi
else
    echo "   📦 Обновление Node.js зависимостей..."
    npm install 2>&1 | tee /tmp/npm-update.log | \
        grep -E "(added|removed|changed|audited|npm WARN|npm ERR|Downloading|Installing|Building)" || true
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo "   ✅ Зависимости обновлены"
    else
        echo "   ⚠️  Возможны проблемы при обновлении"
    fi
fi

echo "✅ Frontend настроен"

# 5. Создание образов контейнеров (опционально)
echo ""
read -p "Создать образы контейнеров для песочниц? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔨 Создание образов контейнеров..."
    
    # Проверяем наличие Podman или Docker
    CONTAINER_CMD=""
    if command -v podman &> /dev/null; then
        CONTAINER_CMD="podman"
        echo "✅ Используется Podman: $(podman --version)"
        
        # Проверяем наличие зависимостей для rootless Podman
        if ! command -v newuidmap &> /dev/null; then
            echo "❌ Ошибка: newuidmap не найден (необходим для rootless Podman)"
            echo "💡 Установите: sudo apt-get install uidmap"
            echo "⚠️  Пропускаем создание образов"
            CONTAINER_CMD=""
        elif ! command -v slirp4netns &> /dev/null; then
            echo "❌ Ошибка: slirp4netns не найден (необходим для rootless Podman)"
            echo "💡 Установите: sudo apt-get install slirp4netns"
            echo "⚠️  Пропускаем создание образов"
            CONTAINER_CMD=""
        elif ! command -v fuse-overlayfs &> /dev/null; then
            echo "❌ Ошибка: fuse-overlayfs не найден (необходим для rootless Podman)"
            echo "💡 Установите: sudo apt-get install fuse-overlayfs"
            echo "⚠️  Пропускаем создание образов"
            CONTAINER_CMD=""
        else
            # Проверяем, работает ли rootless Podman
            if ! $CONTAINER_CMD info &>/dev/null; then
                echo "⚠️  Предупреждение: Podman может быть не настроен для rootless режима"
                echo "💡 Попробуйте: podman system migrate"
                echo "💡 Или выйдите и войдите снова"
                echo ""
                read -p "Продолжить создание образов? (y/n) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    echo "⏭️  Создание образов пропущено"
                    CONTAINER_CMD=""
                fi
            fi
        fi
    elif command -v docker &> /dev/null; then
        CONTAINER_CMD="docker"
        echo "✅ Используется Docker: $(docker --version)"
        
        # Проверяем, может ли пользователь использовать Docker
        if ! docker info &>/dev/null; then
            echo "⚠️  Предупреждение: Пользователь не может использовать Docker"
            echo "💡 Добавьте пользователя в группу docker: sudo usermod -aG docker $USER"
            echo "💡 Затем выйдите и войдите снова"
            echo ""
            read -p "Продолжить создание образов? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "⏭️  Создание образов пропущено"
                CONTAINER_CMD=""
            fi
        fi
    else
        echo "❌ Ошибка: Podman или Docker не найдены"
        echo "💡 Установите один из них:"
        echo "   sudo apt-get install podman uidmap slirp4netns fuse-overlayfs"
        echo "   или"
        echo "   sudo apt-get install docker.io"
        CONTAINER_CMD=""
    fi
    
    if [ -n "$CONTAINER_CMD" ]; then
        echo "Выберите тип образа для создания:"
        echo "  1) Базовый образ (для CLI-миссий B, C)"
        echo "  2) Образ с VNC (для GUI-миссий A)"
        echo "  3) Оба образа"
        echo "  4) Пропустить создание образа"
        read -p "Ваш выбор (1-4): " image_choice
        
        cd "$PROJECT_ROOT/scripts" || {
            echo "❌ Ошибка: не удалось перейти в директорию scripts"
            exit 1
        }
        
        # Проверяем наличие скрипта создания образов
        if [ ! -f "create-astra-image.sh" ]; then
            echo "❌ Ошибка: скрипт create-astra-image.sh не найден"
            echo "💡 Проверьте путь: $PROJECT_ROOT/scripts/create-astra-image.sh"
        else
            IMAGE_CREATION_SUCCESS=true
            
            case $image_choice in
                1)
                    echo "📦 Создание базового образа..."
                    if ! bash create-astra-image.sh 2>&1 | tee /tmp/image-base.log; then
                        echo "❌ Ошибка создания базового образа"
                        echo "💡 Показываем последние строки лога:"
                        tail -30 /tmp/image-base.log 2>/dev/null || true
                        echo "💡 Образ можно создать позже: cd scripts && ./create-astra-image.sh"
                        IMAGE_CREATION_SUCCESS=false
                    else
                        echo "✅ Базовый образ создан"
                    fi
                    ;;
                2)
                    echo "📦 Создание образа с VNC..."
                    if ! bash create-astra-image.sh --vnc 2>&1 | tee /tmp/image-vnc.log; then
                        echo "❌ Ошибка создания VNC образа"
                        echo "💡 Показываем последние строки лога:"
                        tail -30 /tmp/image-vnc.log 2>/dev/null || true
                        echo "💡 Образ можно создать позже: cd scripts && ./create-astra-image.sh --vnc"
                        IMAGE_CREATION_SUCCESS=false
                    else
                        echo "✅ Образ с VNC создан"
                    fi
                    ;;
                3)
                    echo "📦 Создание базового образа..."
                    if ! bash create-astra-image.sh 2>&1 | tee /tmp/image-base.log; then
                        echo "❌ Ошибка создания базового образа"
                        tail -20 /tmp/image-base.log 2>/dev/null || true
                        IMAGE_CREATION_SUCCESS=false
                    else
                        echo "✅ Базовый образ создан"
                    fi
                    echo ""
                    echo "📦 Создание образа с VNC..."
                    if ! bash create-astra-image.sh --vnc 2>&1 | tee /tmp/image-vnc.log; then
                        echo "❌ Ошибка создания образа с VNC"
                        tail -20 /tmp/image-vnc.log 2>/dev/null || true
                        IMAGE_CREATION_SUCCESS=false
                    else
                        echo "✅ Образ с VNC создан"
                    fi
                    ;;
                *)
                    echo "⏭️  Создание образа пропущено"
                    IMAGE_CREATION_SUCCESS=false
                    ;;
            esac
            
            if [ "$image_choice" != "4" ] && [ "$IMAGE_CREATION_SUCCESS" = true ]; then
                echo ""
                echo "📋 Созданные образы:"
                if [ "$CONTAINER_CMD" = "podman" ]; then
                    podman images | grep -E "REPOSITORY|localhost/astra-linux" || podman images | head -5
                else
                    docker images | grep -E "REPOSITORY|localhost/astra-linux" || docker images | head -5
                fi
                echo ""
                echo "💡 Для тестирования образа:"
                if [ "$CONTAINER_CMD" = "podman" ]; then
                    echo "   podman run -d -p 5900:5900 -p 6080:6080 --name test-vnc localhost/astra-linux:vnc"
                else
                    echo "   docker run -d -p 5900:5900 -p 6080:6080 --name test-vnc localhost/astra-linux:vnc"
                fi
            fi
        fi
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

