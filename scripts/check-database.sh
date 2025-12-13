#!/bin/bash
# Скрипт для проверки и настройки базы данных PostgreSQL

set -e

DB_USER="trainer_user"
DB_PASSWORD="trainer_password"
DB_NAME="trainer_db"

echo "🔍 Проверка базы данных PostgreSQL..."
echo ""

# Проверка PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL не установлен"
    echo "💡 Установите: sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

echo "✅ PostgreSQL установлен: $(psql --version | head -1)"
echo ""

# Проверка запуска службы
if ! systemctl is-active --quiet postgresql; then
    echo "⚠️  PostgreSQL не запущен"
    echo "   Запуск службы..."
    sudo systemctl start postgresql || {
        echo "❌ Не удалось запустить PostgreSQL"
        exit 1
    }
    echo "✅ PostgreSQL запущен"
else
    echo "✅ PostgreSQL запущен"
fi
echo ""

# Проверка пользователя
echo "🔍 Проверка пользователя $DB_USER..."
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo "   Создание пользователя $DB_USER..."
    sudo -u postgres createuser "$DB_USER" || {
        echo "❌ Не удалось создать пользователя"
        exit 1
    }
    sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || {
        echo "❌ Не удалось установить пароль"
        exit 1
    }
    echo "✅ Пользователь создан"
else
    echo "✅ Пользователь существует"
fi
echo ""

# Проверка базы данных
echo "🔍 Проверка базы данных $DB_NAME..."
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    echo "   Создание базы данных $DB_NAME..."
    sudo -u postgres createdb -O "$DB_USER" "$DB_NAME" || {
        echo "❌ Не удалось создать базу данных"
        exit 1
    }
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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
echo "✅ База данных настроена и готова к использованию!"
echo ""

