#!/bin/bash
# Скрипт для проверки подключения к PostgreSQL и кодировки базы данных

echo "🔍 Проверка PostgreSQL и базы данных"
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

# Проверка кодировки базы данных (если доступна)
if [ $TCP_AVAILABLE -eq 1 ]; then
    echo "🔍 Проверка кодировки базы данных trainer_db..."
    if sudo -u postgres psql -h localhost -d trainer_db -c "SELECT 1;" &>/dev/null; then
        sudo -u postgres psql -h localhost -d trainer_db << 'EOF' 2>/dev/null || true
SELECT 
    datname as "Database",
    pg_encoding_to_char(encoding) as "Encoding",
    datcollate as "Collate",
    datctype as "Ctype"
FROM pg_database 
WHERE datname = 'trainer_db';

SHOW server_encoding;
SHOW client_encoding;
EOF
        echo ""
        echo "✅ Если Encoding = UTF8, то база данных настроена правильно"
    else
        echo "⚠️  База данных trainer_db не существует или недоступна"
    fi
    echo ""
fi

# Рекомендации
echo "📋 Рекомендации:"
echo ""

if [ $TCP_AVAILABLE -eq 1 ]; then
    echo "✅ PostgreSQL доступен через TCP"
    echo ""
    echo "💡 Для настройки базы данных используйте:"
    echo "   ./scripts/setup-database.sh"
    echo ""
    echo "💡 Для исправления кодировки используйте:"
    echo "   ./scripts/fix-database-encoding.sh"
else
    echo "⚠️  PostgreSQL не доступен через TCP"
    echo ""
    echo "💡 Попробуйте:"
    echo "   1. Запустить PostgreSQL:"
    echo "      sudo service postgresql start"
    echo ""
    echo "   2. Проверить конфигурацию PostgreSQL:"
    echo "      sudo cat /etc/postgresql/*/main/postgresql.conf | grep listen_addresses"
    echo ""
fi

echo ""

