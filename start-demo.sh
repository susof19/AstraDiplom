#!/bin/bash
# Скрипт запуска для демонстрации Astra Linux Training Simulator

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Запуск Astra Linux Training Simulator для демонстрации"
echo "=========================================================="
echo ""

# Проверка образов
echo "📦 Проверка образов..."
if ! podman images | grep -q "astra-linux"; then
    echo "⚠️  Образы не найдены!"
    echo ""
    echo "Создайте образы командой:"
    echo "  cd scripts && ./create-astra-image.sh"
    echo ""
    read -p "Создать базовый образ сейчас? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd scripts
        ./create-astra-image.sh
        cd ..
    else
        exit 1
    fi
fi
echo "✅ Образы найдены"
echo ""

# Проверка зависимостей Backend
echo "🔍 Проверка зависимостей Backend..."
if [ ! -d "backend/venv" ]; then
    echo "⚠️  Виртуальное окружение не найдено"
    echo "Создание venv..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt -q
    cd ..
    echo "✅ Зависимости установлены"
else
    echo "✅ Backend готов"
fi
echo ""

# Проверка зависимостей Frontend
echo "🔍 Проверка зависимостей Frontend..."
if [ ! -d "frontend/web/node_modules" ]; then
    echo "⚠️  Node modules не найдены"
    echo "Установка зависимостей..."
    cd frontend/web
    npm install --silent
    cd ../..
    echo "✅ Зависимости установлены"
else
    echo "✅ Frontend готов"
fi
echo ""

# Остановка старых процессов
echo "🧹 Очистка старых процессов..."
pkill -f 'python.*run.py' 2>/dev/null || true
pkill -f 'npm start' 2>/dev/null || true
pkill -f 'react-scripts start' 2>/dev/null || true
sleep 2
echo "✅ Очистка завершена"
echo ""

# Запуск Backend
echo "🔧 Запуск Backend..."
cd backend
source venv/bin/activate
nohup python run.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend запущен (PID: $BACKEND_PID)"
cd ..

# Ожидание запуска Backend
echo "⏳ Ожидание запуска Backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/missions > /dev/null 2>&1; then
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
cd frontend/web
BROWSER=none nohup npm start > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend запущен (PID: $FRONTEND_PID)"
cd ../..

# Ожидание запуска Frontend
echo "⏳ Ожидание запуска Frontend..."
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend готов"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "⚠️  Frontend не отвечает, проверьте логи: tail -f frontend.log"
    fi
    sleep 1
done
echo ""

echo "=========================================================="
echo "✅ Система запущена и готова к демонстрации!"
echo ""
echo "📍 Адреса:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Логи:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "📊 Контейнеры:"
echo "   podman ps"
echo ""
echo "🛑 Для остановки:"
echo "   ./stop-demo.sh"
echo "   Или: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "🎓 Готово к демонстрации!"
echo ""

# Сохранить PIDs
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Открыть браузер (опционально)
sleep 2
read -p "Открыть браузер? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    xdg-open http://localhost:3000 2>/dev/null || \
    firefox http://localhost:3000 2>/dev/null || \
    chromium http://localhost:3000 2>/dev/null || \
    google-chrome http://localhost:3000 2>/dev/null || \
    echo "Откройте вручную: http://localhost:3000"
fi

echo ""
echo "Система работает в фоновом режиме"
echo "Для остановки используйте: ./stop-demo.sh"

