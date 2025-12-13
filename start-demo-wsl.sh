#!/bin/bash
# Скрипт запуска Linux Training Simulator для WSL

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

echo "🚀 Запуск Linux Training Simulator (WSL)"
echo "=================================================="
echo ""

# Проверка и запуск PostgreSQL
echo "⚙️  Проверка PostgreSQL..."
if ! pg_isready -h localhost -U postgres &>/dev/null; then
    echo "   Запуск PostgreSQL..."
    if command -v service &> /dev/null; then
        sudo service postgresql start 2>/dev/null || {
            echo "⚠️  Не удалось запустить PostgreSQL через service"
            echo "💡 Попробуйте вручную: sudo service postgresql start"
        }
    else
        echo "⚠️  service не найден, запустите PostgreSQL вручную"
    fi
    sleep 2
else
    echo "✅ PostgreSQL запущен"
fi
echo ""

# Запуск Backend
echo "🚀 Запуск Backend..."
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "💡 Запустите: ./scripts/quickstart-wsl.sh"
    exit 1
fi

source venv/bin/activate
nohup python run.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend запущен (PID родительского процесса: $BACKEND_PID)"

# Ждем немного и находим реальный PID процесса uvicorn
sleep 2
REAL_BACKEND_PID=$(pgrep -f 'uvicorn.*main:app|python.*run.py' | head -1)
if [ -n "$REAL_BACKEND_PID" ]; then
    BACKEND_PID=$REAL_BACKEND_PID
    echo "   Реальный PID процесса: $BACKEND_PID"
fi
cd "$PROJECT_ROOT"

# Ожидание запуска Backend
echo "⏳ Ожидание запуска Backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend готов"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  Backend не отвечает, проверьте логи: tail -f backend.log"
    fi
    sleep 1
done
echo ""

# Запуск Frontend
echo "🌐 Запуск Frontend..."
cd "$PROJECT_ROOT/frontend/web"
BROWSER=none nohup npm start > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend запущен (PID родительского процесса: $FRONTEND_PID)"

# Ждем немного и находим реальный PID процесса react-scripts
sleep 3
REAL_FRONTEND_PID=$(pgrep -f 'react-scripts start' | head -1)
if [ -n "$REAL_FRONTEND_PID" ]; then
    FRONTEND_PID=$REAL_FRONTEND_PID
    echo "   Реальный PID процесса: $FRONTEND_PID"
fi
cd "$PROJECT_ROOT"

# Ожидание запуска Frontend
echo "⏳ Ожидание запуска Frontend..."
sleep 5

echo ""
echo "=================================================="
echo "✅ Демонстрация запущена!"
echo ""
echo "📋 Сервисы:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📝 Логи:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 Для остановки:"
echo "   ./stop-demo.sh"
echo "   или"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "=================================================="

# Сохранение PID для остановки
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid
