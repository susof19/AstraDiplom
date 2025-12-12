#!/bin/bash
# Скрипт настройки базы данных PostgreSQL для Linux Training Simulator

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔧 Настройка базы данных PostgreSQL"
echo "=================================================="
echo ""

# Проверка прав
if [ "$EUID" -ne 0 ]; then
    echo "⚠️  Для настройки базы данных требуются права администратора"
    echo "Скрипт будет запрашивать пароль при необходимости"
    echo ""
fi

# Проверка наличия PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL не установлен"
    echo "💡 Установите PostgreSQL:"
    echo "   sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

echo "✅ PostgreSQL установлен"
echo ""

# Проверка, запущен ли PostgreSQL
if ! sudo systemctl is-active --quiet postgresql; then
    echo "⚙️  Запуск PostgreSQL..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

echo "✅ PostgreSQL запущен"
echo ""

# Настройка базы данных
echo "📦 Создание базы данных и пользователя..."
echo ""

DB_NAME="trainer_db"
DB_USER="trainer_user"
DB_PASSWORD="trainer_password"

# Создаем скрипт для настройки БД
DB_SETUP_SCRIPT="/tmp/setup_trainer_db.sql"
cat > "$DB_SETUP_SCRIPT" << EOF
-- Создание пользователя (если не существует)
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
        RAISE NOTICE 'Пользователь $DB_USER создан';
    ELSE
        RAISE NOTICE 'Пользователь $DB_USER уже существует';
    END IF;
END
\$\$;

-- Создание базы данных (если не существует)
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
\c $DB_NAME
GRANT ALL ON SCHEMA public TO $DB_USER;
EOF

# Выполняем скрипт
echo "   Выполнение SQL скрипта..."
if sudo -u postgres psql -f "$DB_SETUP_SCRIPT" 2>&1; then
    echo "✅ База данных и пользователь созданы"
else
    echo "❌ Ошибка создания базы данных"
    echo "💡 Попробуйте выполнить вручную:"
    echo "   sudo -u postgres psql"
    echo "   CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    echo "   CREATE DATABASE $DB_NAME OWNER $DB_USER;"
    echo "   \\q"
    rm -f "$DB_SETUP_SCRIPT"
    exit 1
fi

rm -f "$DB_SETUP_SCRIPT"

echo ""
echo "📋 Инициализация таблиц..."
cd "$PROJECT_ROOT/backend"

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "💡 Сначала запустите: ./scripts/quickstart.sh"
    exit 1
fi

source venv/bin/activate

# Инициализируем базу данных
if python init_db.py; then
    echo "✅ Таблицы созданы успешно"
else
    echo "❌ Ошибка создания таблиц"
    echo "💡 Проверьте соединение с базой данных"
    exit 1
fi

deactivate

echo ""
echo "=================================================="
echo "✅ База данных настроена успешно!"
echo ""
echo "📋 Информация:"
echo "   База данных: $DB_NAME"
echo "   Пользователь: $DB_USER"
echo "   Пароль: $DB_PASSWORD"
echo "   URL: postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"
echo ""
echo "💡 Для изменения настроек отредактируйте:"
echo "   backend/config.py или создайте .env файл"
echo ""

