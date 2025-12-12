#!/bin/bash
# Скрипт запуска для демонстрации Linux Training Simulator
# Поддерживает Debian-based дистрибутивы и Astra Linux

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Определение контейнерной команды (Podman или Docker)
CONTAINER_CMD=""
if command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
elif command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
else
    echo "❌ Ошибка: Podman или Docker не найдены"
    echo "💡 Установите один из них:"
    echo "   sudo apt-get install podman"
    echo "   или"
    echo "   sudo apt-get install docker.io"
    exit 1
fi

echo "🚀 Запуск Linux Training Simulator"
echo "=========================================================="
echo "Контейнерная система: $CONTAINER_CMD"
echo ""

# Проверка образов
echo "📦 Проверка образов контейнеров..."
IMAGE_FOUND=false

# Проверяем наличие образов (поддерживаем разные имена)
if $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep -qE "(localhost/astra-linux|astra-linux)"; then
    IMAGE_FOUND=true
    echo "✅ Образы контейнеров найдены"
elif $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep -qE "(localhost/linux-sandbox|linux-sandbox)"; then
    IMAGE_FOUND=true
    echo "✅ Образы контейнеров найдены"
fi

if [ "$IMAGE_FOUND" = false ]; then
    echo "⚠️  Образы контейнеров не найдены!"
    echo ""
    echo "Образы контейнеров необходимы для запуска песочниц (sandbox'ов)."
    echo "Создайте образы командой:"
    echo "  cd scripts && ./create-astra-image.sh"
    echo ""
    echo "Доступные варианты:"
    echo "  1) Базовый образ (для CLI-миссий)"
    echo "  2) Образ с VNC (для GUI-миссий)"
    echo ""
    read -p "Создать образы сейчас? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd scripts || exit 1
        echo ""
        echo "Выберите тип образа:"
        echo "  1) Базовый образ (CLI)"
        echo "  2) Образ с VNC (GUI)"
        echo "  3) Оба образа"
        read -p "Ваш выбор (1-3): " image_choice
        echo
        
        case $image_choice in
            1)
                ./create-astra-image.sh
                ;;
            2)
                ./create-astra-image.sh --vnc
                ;;
            3)
                ./create-astra-image.sh
                ./create-astra-image.sh --vnc
                ;;
            *)
                echo "❌ Неверный выбор"
                exit 1
                ;;
        esac
        
        cd ..
        
        # Проверяем снова после создания
        if ! $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep -qE "(localhost/astra-linux|astra-linux)"; then
            echo "⚠️  Образы не были созданы успешно"
            echo "💡 Продолжаем без образов (некоторые функции могут быть недоступны)"
        else
            echo "✅ Образы созданы успешно"
        fi
    else
        echo "⚠️  Продолжаем без образов (некоторые функции могут быть недоступны)"
        echo "💡 Вы можете создать образы позже: cd scripts && ./create-astra-image.sh"
    fi
fi
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
echo "   $CONTAINER_CMD ps"
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

