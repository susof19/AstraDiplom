#!/bin/bash
# Скрипт для исправления кодировки базы данных PostgreSQL
# Используется для решения проблемы UnicodeDecodeError
# Использует TCP подключение через localhost (как в backend)

# Не используем set -e, чтобы обработать ошибки вручную

echo "🔧 Исправление кодировки базы данных PostgreSQL"
echo "=================================================="
echo ""

# Проверка PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL не установлен"
    exit 1
fi

# Проверка и запуск PostgreSQL
echo "🔍 Проверка статуса PostgreSQL..."
if ! pg_isready -h localhost -U postgres &>/dev/null; then
    echo "⚠️  PostgreSQL не запущен, пытаемся запустить..."
    
    if command -v service &> /dev/null; then
        sudo service postgresql start 2>/dev/null || {
            echo "❌ Не удалось запустить PostgreSQL через service"
            echo "💡 Попробуйте вручную: sudo service postgresql start"
            exit 1
        }
    elif command -v systemctl &> /dev/null; then
        sudo systemctl start postgresql 2>/dev/null || {
            echo "❌ Не удалось запустить PostgreSQL через systemctl"
            echo "💡 Попробуйте вручную: sudo systemctl start postgresql"
            exit 1
        }
    else
        echo "❌ Не найден способ запуска PostgreSQL (service или systemctl)"
        echo "💡 Запустите PostgreSQL вручную и повторите попытку"
        exit 1
    fi
    
    echo "⏳ Ожидание запуска PostgreSQL..."
    sleep 3
    
    # Проверяем еще раз
    if ! pg_isready -h localhost -U postgres &>/dev/null; then
        echo "❌ PostgreSQL все еще не отвечает"
        echo "💡 Проверьте логи: sudo tail -f /var/log/postgresql/postgresql-*-main.log"
        exit 1
    fi
fi

echo "✅ PostgreSQL запущен и доступен через TCP (localhost:5432)"
echo ""

echo "⚠️  ВНИМАНИЕ: Этот скрипт пересоздаст базу данных trainer_db"
echo "   Все данные будут удалены!"
echo ""
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Отменено"
    exit 0
fi

echo ""
echo "📋 Шаги исправления:"
echo "   1. Закрытие всех подключений к базе данных"
echo "   2. Удаление старой базы данных"
echo "   3. Создание новой базы данных с кодировкой UTF-8"
echo ""

# Закрытие всех подключений к базе данных
echo "🔌 Закрытие подключений к базе данных..."
# Используем sudo -u postgres с указанием хоста (обходит проблему с паролем)
sudo -u postgres psql -h localhost -d postgres << 'EOF' 2>/dev/null || true
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'trainer_db' AND pid <> pg_backend_pid();
EOF

# Удаление старой базы данных
echo "🗑️  Удаление старой базы данных..."
sudo -u postgres psql -h localhost -d postgres << 'EOF' 2>/dev/null || true
DROP DATABASE IF EXISTS trainer_db;
EOF

# Создание пользователя (если не существует)
echo "👤 Создание пользователя trainer_user..."
sudo -u postgres psql -h localhost -d postgres << 'EOF' 2>/dev/null || true
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'trainer_user') THEN
        CREATE USER trainer_user WITH PASSWORD 'trainer_password';
    END IF;
END
$$;
EOF

# Создание новой базы данных с правильной кодировкой
echo "📦 Создание новой базы данных с кодировкой UTF-8..."
echo "   Используется подключение через TCP (localhost:5432)"

# Создаем базу данных с кодировкой UTF-8 без указания локали
# ENCODING 'UTF8' гарантирует правильную кодировку независимо от локали
echo "   Создаем базу данных с кодировкой UTF-8 (без указания локали)"
sudo -u postgres psql -h localhost -d postgres << 'EOF'
CREATE DATABASE trainer_db 
    OWNER trainer_user 
    ENCODING 'UTF8'
    TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE trainer_db TO trainer_user;
EOF

if [ $? -ne 0 ]; then
    echo "❌ Ошибка при создании базы данных"
    echo ""
    echo "💡 Выполните команды вручную:"
    echo ""
    echo "   sudo -u postgres psql -h localhost"
    echo "   CREATE DATABASE trainer_db OWNER trainer_user ENCODING 'UTF8' TEMPLATE template0;"
    echo "   GRANT ALL PRIVILEGES ON DATABASE trainer_db TO trainer_user;"
    echo "   \\q"
    exit 1
fi

echo ""
echo "✅ База данных пересоздана с кодировкой UTF-8"
echo ""
echo "📋 Следующие шаги:"
echo "   1. Инициализируйте структуру базы данных:"
echo "      cd backend"
echo "      source venv/bin/activate"
echo "      python init_db.py"
echo ""
echo "   2. Перезапустите backend"
echo ""
