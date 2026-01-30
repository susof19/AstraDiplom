#!/bin/bash
# Скрипт проверки и настройки базы данных PostgreSQL (Windows-hosted, WSL client)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DB_HOST="localhost"
DB_PORT="5432"

DB_ADMIN_USER="postgres"
DB_ADMIN_PASSWORD="admin1234"

DB_USER="trainer_user"
DB_PASSWORD="trainer_password"
DB_NAME="trainer_db"

export PGPASSWORD="$DB_ADMIN_PASSWORD"

echo "🔧 Проверка и настройка базы данных PostgreSQL (TCP)"
echo "=================================================="
echo ""

# Проверка psql
if ! command -v psql &> /dev/null; then
    echo "❌ psql не установлен"
    exit 1
fi

echo "✅ psql найден: $(psql --version | head -1)"
echo ""

# Проверка соединения с сервером
echo "🔍 Проверка подключения к PostgreSQL ($DB_HOST:$DB_PORT)..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -d postgres -c "SELECT 1;" &>/dev/null; then
    echo "❌ Не удалось подключиться к PostgreSQL"
    echo "💡 Убедись, что PostgreSQL запущен в Windows"
    exit 1
fi
echo "✅ Соединение с PostgreSQL установлено"
echo ""

# Проверка и создание пользователя
echo "🔍 Проверка пользователя $DB_USER..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then

    echo "   Создание пользователя $DB_USER..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -c \
        "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

    echo "✅ Пользователь создан"
else
    echo "✅ Пользователь существует"
fi
echo ""

# Проверка и создание базы данных
echo "🔍 Проверка базы данных $DB_NAME..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -tAc \
    "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then

    echo "   Создание базы данных $DB_NAME..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -c \
        "CREATE DATABASE $DB_NAME OWNER $DB_USER ENCODING 'UTF8';"

    echo "✅ База данных создана"
else
    echo "✅ База данных существует"
fi
echo ""

# Проверка подключения под пользователем проекта
echo "🔍 Проверка подключения пользователя $DB_USER..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &>/dev/null || {
    echo "❌ Пользователь не может подключиться к БД"
    exit 1
}
echo "✅ Подключение успешно"
echo ""

# Инициализация таблиц
echo "📦 Инициализация таблиц..."
cd "$PROJECT_ROOT/backend"

if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    exit 1
fi

source venv/bin/activate
python init_db.py
deactivate

echo ""
echo "=================================================="
echo "✅ База данных полностью готова!"
echo ""
echo "📋 Данные подключения:"
echo "   postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
