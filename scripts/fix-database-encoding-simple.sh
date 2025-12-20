#!/bin/bash
# Упрощенный скрипт для исправления кодировки базы данных PostgreSQL
# Использует тот же метод подключения, что и backend (TCP через localhost)

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
            echo "❌ Не удалось запустить PostgreSQL"
            echo "💡 Попробуйте вручную: sudo service postgresql start"
            exit 1
        }
        sleep 3
    fi
fi

if ! pg_isready -h localhost -U postgres &>/dev/null; then
    echo "❌ PostgreSQL не отвечает на localhost:5432"
    echo "💡 Проверьте, что PostgreSQL запущен и слушает на localhost"
    exit 1
fi

echo "✅ PostgreSQL запущен и доступен"
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
echo "📋 Выполнение операций через TCP (localhost:5432)..."
echo ""

# Используем подключение через TCP, как в backend
# Сначала пробуем без пароля (trust authentication для localhost)
# Если не работает, попробуем с пустым паролем

# Функция для выполнения SQL команд
execute_sql() {
    local sql_command="$1"
    # Пробуем несколько методов подключения
    if PGPASSWORD='' psql -h localhost -U postgres -d postgres -c "$sql_command" 2>/dev/null; then
        return 0
    elif sudo -u postgres psql -h localhost -d postgres -c "$sql_command" 2>/dev/null; then
        return 0
    else
        # Последняя попытка - через Unix socket
        sudo -u postgres psql -d postgres -c "$sql_command" 2>/dev/null
        return $?
    fi
}

# Закрытие подключений
echo "🔌 Закрытие подключений к базе данных..."
execute_sql "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'trainer_db' AND pid <> pg_backend_pid();" || true

# Удаление базы данных
echo "🗑️  Удаление старой базы данных..."
execute_sql "DROP DATABASE IF EXISTS trainer_db;" || true

# Создание новой базы данных
echo "📦 Создание новой базы данных с кодировкой UTF-8..."

# Пробуем создать базу данных разными способами
SUCCESS=0

# Способ 1: через TCP с пустым паролем
if PGPASSWORD='' psql -h localhost -U postgres -d postgres << 'EOF' 2>/dev/null; then
CREATE DATABASE trainer_db 
    OWNER trainer_user 
    ENCODING 'UTF8' 
    LC_COLLATE='C' 
    LC_CTYPE='C'
    TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE trainer_db TO trainer_user;
EOF
    SUCCESS=1
# Способ 2: через sudo
elif sudo -u postgres psql -h localhost -d postgres << 'EOF' 2>/dev/null; then
CREATE DATABASE trainer_db 
    OWNER trainer_user 
    ENCODING 'UTF8' 
    LC_COLLATE='C' 
    LC_CTYPE='C'
    TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE trainer_db TO trainer_user;
EOF
    SUCCESS=1
# Способ 3: через Unix socket
elif sudo -u postgres psql -d postgres << 'EOF' 2>/dev/null; then
CREATE DATABASE trainer_db 
    OWNER trainer_user 
    ENCODING 'UTF8' 
    LC_COLLATE='C' 
    LC_CTYPE='C'
    TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE trainer_db TO trainer_user;
EOF
    SUCCESS=1
fi

if [ $SUCCESS -eq 0 ]; then
    echo "❌ Не удалось создать базу данных автоматически"
    echo ""
    echo "💡 Выполните команды вручную:"
    echo ""
    echo "   PGPASSWORD='' psql -h localhost -U postgres"
    echo "   CREATE DATABASE trainer_db OWNER trainer_user ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE template0;"
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
