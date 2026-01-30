#!/bin/bash
# Скрипт для проверки и настройки подключения к PostgreSQL

echo "🔍 Проверка PostgreSQL"
echo "=================================================="
echo ""

# Проверка установки
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL клиент не установлен"
    exit 1
fi

echo "✅ PostgreSQL клиент установлен: $(psql --version | head -1)"
echo ""

# Проверка статуса сервиса
echo "📋 Проверка статуса сервиса PostgreSQL..."
if command -v service &> /dev/null; then
    sudo service postgresql status 2>/dev/null || echo "⚠️  Не удалось проверить статус через service"
elif command -v systemctl &> /dev/null; then
    sudo systemctl status postgresql 2>/dev/null || echo "⚠️  Не удалось проверить статус через systemctl"
fi
echo ""

# Проверка доступности через TCP
echo "🌐 Проверка подключения через TCP (localhost:5432)..."
if pg_isready -h localhost -U postgres &>/dev/null; then
    echo "✅ PostgreSQL доступен через TCP на localhost:5432"
    TCP_AVAILABLE=1
else
    echo "❌ PostgreSQL недоступен через TCP на localhost:5432"
    TCP_AVAILABLE=0
fi
echo ""

# Проверка Unix socket
echo "🔌 Проверка Unix socket..."
SOCKET_PATH="/var/run/postgresql/.s.PGSQL.5432"
if [ -S "$SOCKET_PATH" ]; then
    echo "✅ Unix socket найден: $SOCKET_PATH"
    SOCKET_AVAILABLE=1
else
    echo "⚠️  Unix socket не найден: $SOCKET_PATH"
    SOCKET_AVAILABLE=0
    
    # Ищем socket в других местах
    echo "   Поиск socket в других местах..."
    find /var/run/postgresql /tmp -name ".s.PGSQL.*" 2>/dev/null | head -3 || echo "   Socket не найден"
fi
echo ""

# Рекомендации
echo "📋 Рекомендации:"
echo ""

if [ $TCP_AVAILABLE -eq 1 ]; then
    echo "✅ Используйте подключение через TCP:"
    echo "   PGPASSWORD='' psql -h localhost -U postgres"
    echo "   или"
    echo "   psql -h localhost -U postgres -d postgres"
    echo ""
    echo "   Для создания базы данных:"
    echo "   PGPASSWORD='' psql -h localhost -U postgres << 'EOF'"
    echo "   CREATE DATABASE trainer_db OWNER trainer_user ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE template0;"
    echo "   GRANT ALL PRIVILEGES ON DATABASE trainer_db TO trainer_user;"
    echo "   EOF"
elif [ $SOCKET_AVAILABLE -eq 1 ]; then
    echo "✅ Используйте подключение через Unix socket:"
    echo "   sudo -u postgres psql"
    echo ""
else
    echo "⚠️  PostgreSQL не доступен ни через TCP, ни через Unix socket"
    echo ""
    echo "💡 Попробуйте:"
    echo "   1. Запустить PostgreSQL:"
    echo "      sudo service postgresql start"
    echo ""
    echo "   2. Проверить конфигурацию PostgreSQL:"
    echo "      sudo cat /etc/postgresql/*/main/postgresql.conf | grep listen_addresses"
    echo "      sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -v '^#' | grep -v '^$'"
    echo ""
fi

echo ""
echo "🔧 Для исправления базы данных используйте:"
echo "   ./scripts/fix-database-encoding-simple.sh"
echo "   или выполните команды вручную (см. рекомендации выше)"
echo ""
