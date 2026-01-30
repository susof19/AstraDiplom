#!/bin/bash
# Скрипт для проверки кодировки базы данных PostgreSQL

echo "🔍 Проверка кодировки базы данных PostgreSQL"
echo "=================================================="
echo ""

# Проверка подключения и кодировки
sudo -u postgres psql -h localhost -d trainer_db << 'EOF'
-- Проверка кодировки базы данных
SELECT 
    datname as "Database",
    pg_encoding_to_char(encoding) as "Encoding",
    datcollate as "Collate",
    datctype as "Ctype"
FROM pg_database 
WHERE datname = 'trainer_db';

-- Проверка кодировки текущего подключения
SHOW server_encoding;
SHOW client_encoding;
EOF

echo ""
echo "✅ Если Encoding = UTF8, то база данных настроена правильно"
echo ""
