#!/bin/bash
# Скрипт для сброса прогресса всех пользователей
# Удаляет все файлы прогресса, чтобы начать с нуля

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔄 Сброс прогресса пользователей"
echo "=================================================="
echo ""

PROGRESS_DIR="$PROJECT_ROOT/sandbox_data"

if [ ! -d "$PROGRESS_DIR" ]; then
    echo "✅ Директория прогресса не существует, ничего не нужно сбрасывать"
    exit 0
fi

# Подсчитываем файлы прогресса
PROGRESS_FILES=$(find "$PROGRESS_DIR" -name "progress_*.json" 2>/dev/null | wc -l)

if [ "$PROGRESS_FILES" -eq 0 ]; then
    echo "✅ Файлы прогресса не найдены, ничего не нужно сбрасывать"
    exit 0
fi

echo "⚠️  ВНИМАНИЕ: Будет удалено $PROGRESS_FILES файл(ов) прогресса"
echo "   Все данные о прогрессе пользователей будут потеряны!"
echo ""
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Отменено"
    exit 0
fi

echo ""
echo "🗑️  Удаление файлов прогресса..."

# Удаляем все файлы прогресса
find "$PROGRESS_DIR" -name "progress_*.json" -type f -delete

if [ $? -eq 0 ]; then
    echo "✅ Прогресс всех пользователей сброшен"
    echo ""
    echo "📋 Следующие шаги:"
    echo "   1. Перезапустите backend"
    echo "   2. Пользователи начнут с нулевого прогресса"
    echo ""
else
    echo "❌ Ошибка при удалении файлов прогресса"
    exit 1
fi
