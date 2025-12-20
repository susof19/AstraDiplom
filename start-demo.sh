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

# Функция для проверки наличия образов
check_images() {
    # Получаем список всех образов (используем обычный вывод для надежности)
    local images_output
    images_output=$($CONTAINER_CMD images 2>/dev/null)
    
    if [ -z "$images_output" ]; then
        return 1
    fi
    
    # Проверяем наличие образов по имени репозитория (первая колонка)
    # Ищем: localhost/linux-gui-vnc, localhost/linux-base, localhost/astra-linux, localhost/linux-sandbox
    if echo "$images_output" | awk 'NR>1 {print $1}' | grep -qE "^(localhost/)?(linux-gui-vnc|linux-base|astra-linux|linux-sandbox)$"; then
        return 0
    fi
    
    # Также проверяем полные имена с тегами в первой колонке
    if echo "$images_output" | awk 'NR>1 {print $1}' | grep -qE "(localhost/)?(linux-gui-vnc|linux-base|astra-linux|linux-sandbox)"; then
        return 0
    fi
    
    return 1
}

IMAGE_FOUND=false
if check_images; then
    IMAGE_FOUND=true
    echo "✅ Образы контейнеров найдены:"
    # Показываем найденные образы
    echo ""
    if $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -E "(localhost/linux-gui-vnc|localhost/linux-base|localhost/astra-linux|localhost/linux-sandbox)" 2>/dev/null | head -5; then
        : # Успешно показали через форматированный вывод
    else
        # Fallback: показываем через обычный вывод
        $CONTAINER_CMD images 2>/dev/null | grep -E "(REPOSITORY|localhost/linux-gui-vnc|localhost/linux-base|localhost/astra-linux|localhost/linux-sandbox|astra-linux.*se|astra-linux.*vnc|linux-sandbox.*base|linux-sandbox.*vnc|linux-gui-vnc|linux-base)" | head -5
    fi
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
        if check_images; then
            echo "✅ Образы созданы успешно"
            echo ""
            echo "📋 Созданные образы:"
            $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -E "(localhost/astra-linux|localhost/linux-sandbox|^astra-linux|^linux-sandbox)" || \
            $CONTAINER_CMD images | grep -E "(REPOSITORY|localhost/astra-linux|localhost/linux-sandbox|astra-linux|linux-sandbox)" | head -5
        else
            echo "⚠️  Образы не были созданы успешно"
            echo "💡 Продолжаем без образов (некоторые функции могут быть недоступны)"
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

# Получение IP адресов для доступа из локальной сети
echo "🌐 Определение сетевых адресов..."
HOST_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "")

# Если не удалось получить IP, пробуем альтернативные методы
if [ -z "$HOST_IP" ]; then
    HOST_IP=$(ip addr show | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0.1' | head -1 || echo "")
fi

if [ -z "$HOST_IP" ]; then
    HOST_IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}' || echo "")
fi

if [ -n "$HOST_IP" ]; then
    echo "   Host IP: $HOST_IP"
else
    echo "   ⚠️  Не удалось определить IP адрес"
fi
echo ""

# Формируем список дополнительных origins для CORS
ADDITIONAL_ORIGINS_LIST=""
if [ -n "$HOST_IP" ]; then
    ADDITIONAL_ORIGINS_LIST="http://${HOST_IP}:3000"
fi

# Остановка старых процессов
echo "🧹 Очистка старых процессов..."
pkill -f 'python.*run.py' 2>/dev/null || true
pkill -f 'uvicorn.*main:app' 2>/dev/null || true
pkill -f 'react-scripts start' 2>/dev/null || true
sleep 2
echo "✅ Очистка завершена"
echo ""

# Запуск Backend
echo "🔧 Запуск Backend..."
cd backend
source venv/bin/activate

# Устанавливаем переменную окружения для дополнительных origins
if [ -n "$ADDITIONAL_ORIGINS_LIST" ]; then
    export ADDITIONAL_ORIGINS="$ADDITIONAL_ORIGINS_LIST"
    echo "   Настроены дополнительные CORS origins: $ADDITIONAL_ORIGINS_LIST"
fi

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
cd ..

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
cd frontend/web
# Настраиваем frontend на прослушивание всех интерфейсов (0.0.0.0)
# Это позволит подключаться с других машин в локальной сети
# Настройки находятся в .env файле (HOST=0.0.0.0)
BROWSER=none nohup npm start > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend запущен (PID родительского процесса: $FRONTEND_PID)"
echo "   Frontend слушает на всех интерфейсах (0.0.0.0:3000)"

# Ждем немного и находим реальный PID процесса react-scripts
sleep 3
REAL_FRONTEND_PID=$(pgrep -f 'react-scripts start' | head -1)
if [ -n "$REAL_FRONTEND_PID" ]; then
    FRONTEND_PID=$REAL_FRONTEND_PID
    echo "   Реальный PID процесса: $FRONTEND_PID"
fi
cd ../..

# Ожидание запуска Frontend
echo "⏳ Ожидание запуска Frontend..."
for i in {1..68}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend готов"
        break
    fi
    if [ $i -eq 45 ]; then
        echo "⚠️  Frontend не отвечает, проверьте логи: tail -f frontend.log"
    fi
    sleep 1
done
echo ""

# Диагностика сетевых подключений
echo "🔍 Диагностика сетевых подключений..."
echo ""

# Проверка прослушивания портов
echo "   Проверка портов:"
if command -v netstat &> /dev/null; then
    LISTENING_PORTS=$(netstat -tuln 2>/dev/null | grep -E ":(3000|8000)" | grep "0.0.0.0" || echo "")
    if [ -n "$LISTENING_PORTS" ]; then
        echo "   ✅ Порты слушают на 0.0.0.0:"
        echo "$LISTENING_PORTS" | while read line; do
            echo "      $line"
        done
    else
        echo "   ⚠️  Порты могут не слушать на всех интерфейсах"
        echo "   💡 Проверьте: netstat -tuln | grep -E ':(3000|8000)'"
    fi
elif command -v ss &> /dev/null; then
    LISTENING_PORTS=$(ss -tuln 2>/dev/null | grep -E ":(3000|8000)" | grep "0.0.0.0" || echo "")
    if [ -n "$LISTENING_PORTS" ]; then
        echo "   ✅ Порты слушают на 0.0.0.0:"
        echo "$LISTENING_PORTS" | while read line; do
            echo "      $line"
        done
    else
        echo "   ⚠️  Порты могут не слушать на всех интерфейсах"
        echo "   💡 Проверьте: ss -tuln | grep -E ':(3000|8000)'"
    fi
else
    echo "   ⚠️  netstat/ss не найдены, пропускаем проверку портов"
fi
echo ""

echo "=========================================================="
echo "✅ Система запущена и готова к демонстрации!"
echo ""
echo "📋 Сервисы (локальный доступ):"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""

# Выводим информацию о доступе из локальной сети
if [ -n "$HOST_IP" ]; then
    echo "🌐 Доступ из локальной сети:"
    echo "   Frontend: http://${HOST_IP}:3000"
    echo "   Backend:  http://${HOST_IP}:8000"
    echo ""
    echo "💡 Убедитесь, что:"
    echo "   1. Firewall разрешает подключения на портах 3000 и 8000"
    echo "   2. Оба устройства в одной локальной сети"
    echo ""
fi

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

