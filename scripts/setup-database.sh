#!/bin/bash
# Скрипт проверки и настройки базы данных PostgreSQL

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DB_USER="trainer_user"
DB_PASSWORD="trainer_password"
DB_NAME="trainer_db"

echo "🔧 Проверка и настройка базы данных PostgreSQL"
echo "=================================================="
echo ""

# Проверка PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL не установлен"
    echo "💡 Установите: sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

echo "✅ PostgreSQL установлен: $(psql --version | head -1)"
echo ""

# Проверка и запуск службы
if command -v systemctl &> /dev/null; then
    if ! sudo systemctl is-active --quiet postgresql; then
        echo "⚠️  PostgreSQL не запущен"
        echo "   Запуск службы..."
        sudo systemctl start postgresql || {
            echo "❌ Не удалось запустить PostgreSQL"
            exit 1
        }
        sudo systemctl enable postgresql 2>/dev/null || true
        echo "✅ PostgreSQL запущен"
    else
        echo "✅ PostgreSQL запущен"
    fi
elif command -v service &> /dev/null; then
    if ! sudo service postgresql status &>/dev/null; then
        echo "⚠️  PostgreSQL не запущен"
        echo "   Запуск службы..."
        sudo service postgresql start || {
            echo "❌ Не удалось запустить PostgreSQL"
            exit 1
        }
        echo "✅ PostgreSQL запущен"
    else
        echo "✅ PostgreSQL запущен"
    fi
else
    echo "⚠️  Не найден способ проверки статуса PostgreSQL"
    echo "   Убедитесь, что PostgreSQL запущен вручную"
fi
echo ""

# Проверка и создание пользователя
echo "🔍 Проверка пользователя $DB_USER..."
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" 2>/dev/null | grep -q 1; then
    echo "   Создание пользователя $DB_USER..."
    sudo -u postgres createuser "$DB_USER" 2>/dev/null || true
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || {
        echo "❌ Не удалось установить пароль"
        exit 1
    }
    echo "✅ Пользователь создан"
else
    echo "✅ Пользователь существует"
fi
echo ""

# Проверка и создание базы данных
echo "🔍 Проверка базы данных $DB_NAME..."
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null | grep -q 1; then
    echo "   Создание базы данных $DB_NAME..."
    sudo -u postgres createdb -O "$DB_USER" -E UTF8 -T template0 "$DB_NAME" 2>/dev/null || {
        echo "❌ Не удалось создать базу данных"
        exit 1
    }
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true
    echo "✅ База данных создана"
else
    echo "✅ База данных существует"
fi
echo ""

# Проверка подключения
echo "🔍 Проверка подключения..."
if PGPASSWORD="$DB_PASSWORD" psql -h localhost -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null; then
    echo "✅ Подключение успешно"
else
    echo "❌ Не удалось подключиться к базе данных"
    echo "💡 Проверьте настройки в backend/config.py"
    exit 1
fi
echo ""

# Инициализация таблиц
echo "📦 Инициализация таблиц..."
cd "$PROJECT_ROOT/backend"

if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "💡 Запустите: ./scripts/quickstart.sh"
    exit 1
fi

source venv/bin/activate
python init_db.py || {
    echo "❌ Ошибка при инициализации таблиц"
    exit 1
}
deactivate

echo ""
echo "=================================================="
echo "✅ База данных настроена и готова к использованию!"
echo ""
echo "📋 Информация:"
echo "   База данных: $DB_NAME"
echo "   Пользователь: $DB_USER"
echo "   Пароль: $DB_PASSWORD"
echo "   URL: postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
echo ""
