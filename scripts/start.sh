#!/bin/bash
# Скрипт запуска всего приложения

set -e

echo "🚀 Запуск Astra Linux Training Simulator"

# Проверка зависимостей
echo "Проверка зависимостей..."

if ! command -v podman &> /dev/null; then
    echo "❌ Podman не установлен"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Node.js/npm не установлен"
    exit 1
fi

echo "✅ Все зависимости установлены"

# Запуск backend
echo "📦 Запуск backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "Запуск API сервера..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

cd ..

# Запуск frontend
echo "🌐 Запуск frontend..."
cd frontend/web
if [ ! -d "node_modules" ]; then
    echo "Установка зависимостей..."
    npm install
fi

echo "Запуск dev сервера..."
npm start &
FRONTEND_PID=$!

cd ../..

echo ""
echo "✅ Приложение запущено!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Для остановки нажмите Ctrl+C"

# Ожидание сигнала
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait

