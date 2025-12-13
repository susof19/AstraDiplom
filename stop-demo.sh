#!/bin/bash
# Скрипт остановки демонстрации Linux Training Simulator

# Определение контейнерной команды (Podman или Docker)
CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
fi

echo "🛑 Остановка Linux Training Simulator..."
echo ""

# Остановка по PID файлам (если есть)
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    echo "Остановка Backend (PID из файла: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || echo "  Процесс $BACKEND_PID уже остановлен"
    rm -f .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    echo "Остановка Frontend (PID из файла: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null || echo "  Процесс $FRONTEND_PID уже остановлен"
    rm -f .frontend.pid
fi

# Остановка процессов по имени (более надежный способ)
echo ""
echo "Очистка процессов по имени..."

# Backend процессы
echo "  Остановка Backend процессов..."
pkill -f 'python.*run.py' 2>/dev/null && echo "    ✅ Backend процессы остановлены" || echo "    ℹ️  Backend процессы не найдены"
pkill -f 'uvicorn.*main:app' 2>/dev/null && echo "    ✅ Uvicorn процессы остановлены" || true
pkill -f 'python.*backend.*run' 2>/dev/null && echo "    ✅ Backend Python процессы остановлены" || true

# Frontend процессы
echo "  Остановка Frontend процессов..."
pkill -f 'react-scripts start' 2>/dev/null && echo "    ✅ Frontend процессы остановлены" || echo "    ℹ️  Frontend процессы не найдены"
pkill -f 'node.*react-scripts' 2>/dev/null && echo "    ✅ React Scripts процессы остановлены" || true

# Дополнительная очистка (на случай, если что-то осталось)
sleep 1
pkill -f 'npm start' 2>/dev/null || true

# Остановка контейнеров (опционально)
if [ -n "$CONTAINER_CMD" ]; then
read -p "Остановить все контейнеры? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Остановка контейнеров..."
        $CONTAINER_CMD stop $($CONTAINER_CMD ps -q) 2>/dev/null || echo "  Нет запущенных контейнеров"
    fi
fi

echo ""
echo "✅ Остановка завершена"
echo ""
echo "Для повторного запуска используйте:"
echo "   ./start-demo.sh       (для Linux)"
echo "   ./start-demo-wsl.sh   (для WSL)"

