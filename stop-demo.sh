#!/bin/bash
# Скрипт остановки демонстрации

echo "🛑 Остановка Astra Linux Training Simulator..."
echo ""

# Остановка по PID файлам
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "Остановка Backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || echo "  Backend уже остановлен"
    rm -f .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "Остановка Frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || echo "  Frontend уже остановлен"
    rm -f .frontend.pid
fi

# Дополнительная очистка процессов
echo "Очистка процессов..."
pkill -f 'python.*run.py' 2>/dev/null || true
pkill -f 'npm start' 2>/dev/null || true
pkill -f 'react-scripts start' 2>/dev/null || true

# Остановка контейнеров (опционально)
read -p "Остановить все контейнеры? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Остановка контейнеров..."
    podman stop $(podman ps -q) 2>/dev/null || echo "  Нет запущенных контейнеров"
fi

echo ""
echo "✅ Остановка завершена"
echo ""
echo "Для повторного запуска используйте: ./start-demo.sh"

