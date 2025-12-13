#!/bin/bash
# Скрипт запуска Linux Training Simulator для WSL

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

echo "🚀 Запуск Linux Training Simulator (WSL)"
echo "=================================================="
echo ""

# Определение контейнерной команды (Docker или Podman)
CONTAINER_CMD=""
if command -v docker &> /dev/null; then
    CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
    CONTAINER_CMD="podman"
fi

# Функция проверки наличия образа
check_image_exists() {
    local image_name="$1"
    if [ -z "$CONTAINER_CMD" ]; then
        return 1
    fi
    $CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -q "^${image_name}\|^localhost/${image_name}" || \
    $CONTAINER_CMD images 2>/dev/null | awk 'NR>1 {print $1":"$2}' | grep -q "^${image_name}\|^localhost/${image_name}"
}

# Функция выбора образа
select_image() {
    echo "📦 Выбор образа для использования:"
    echo ""
    
    # Список образов для проверки
    GUI_IMAGES=(
        "localhost/linux-gui-vnc:debian:Debian 12"
        "localhost/linux-gui-vnc:ubuntu:Ubuntu 22.04"
        "localhost/astra-vnc:latest:Astra Linux (готовый образ)"
        "localhost/linux-gui-vnc:astra:Astra Linux (собранный)"
    )
    
    # Проверяем доступные образы
    AVAILABLE_OPTIONS=()
    AVAILABLE_NAMES=()
    
    count=0
    for img_entry in "${GUI_IMAGES[@]}"; do
        img_name=$(echo "$img_entry" | cut -d':' -f1)
        tag=$(echo "$img_entry" | cut -d':' -f2)
        distro_name=$(echo "$img_entry" | cut -d':' -f3-)
        full_img="${img_name}:${tag}"
        if check_image_exists "$full_img"; then
            AVAILABLE_OPTIONS[$count]="$full_img"
            AVAILABLE_NAMES[$count]="$distro_name"
            count=$((count + 1))
        fi
    done
    
    if [ $count -eq 0 ]; then
        echo "⚠️  Доступные образы не найдены!"
        echo ""
        echo "Какой образ вы хотите создать?"
        echo "  1) Debian 12 (рекомендуется для начала)"
        echo "  2) Ubuntu 22.04"
        echo "  3) Astra Linux (готовый образ из репозитория)"
        echo "  4) Пропустить (песочницы будут недоступны)"
        echo ""
        read -p "Выберите вариант (1-4): " choice
        echo ""
        
        case $choice in
            1)
                SELECTED_DISTRO="debian"
                echo "🔨 Создание образа Debian 12..."
                cd "$PROJECT_ROOT/scripts"
                echo "2" | ./create-astra-image.sh --vnc
                cd "$PROJECT_ROOT"
                # Сохраняем выбор в .env
                BACKEND_ENV="$PROJECT_ROOT/backend/.env"
                if [ -f "$BACKEND_ENV" ]; then
                    sed -i '/^DEFAULT_DISTRO=/d' "$BACKEND_ENV" 2>/dev/null || sed -i.bak '/^DEFAULT_DISTRO=/d' "$BACKEND_ENV"
                fi
                echo "DEFAULT_DISTRO=$SELECTED_DISTRO" >> "$BACKEND_ENV"
                echo "💡 Дистрибутив '$SELECTED_DISTRO' сохранен в backend/.env"
                ;;
            2)
                SELECTED_DISTRO="ubuntu"
                echo "🔨 Создание образа Ubuntu 22.04..."
                cd "$PROJECT_ROOT/scripts"
                echo "3" | ./create-astra-image.sh --vnc
                cd "$PROJECT_ROOT"
                # Сохраняем выбор в .env
                BACKEND_ENV="$PROJECT_ROOT/backend/.env"
                if [ -f "$BACKEND_ENV" ]; then
                    sed -i '/^DEFAULT_DISTRO=/d' "$BACKEND_ENV" 2>/dev/null || sed -i.bak '/^DEFAULT_DISTRO=/d' "$BACKEND_ENV"
                fi
                echo "DEFAULT_DISTRO=$SELECTED_DISTRO" >> "$BACKEND_ENV"
                echo "💡 Дистрибутив '$SELECTED_DISTRO' сохранен в backend/.env"
                ;;
            3)
                SELECTED_DISTRO="astra"
                echo "🔨 Настройка образа Astra Linux..."
                cd "$PROJECT_ROOT/scripts"
                ./setup-astra-vnc-image.sh
                cd "$PROJECT_ROOT"
                # Сохраняем выбор в .env
                BACKEND_ENV="$PROJECT_ROOT/backend/.env"
                if [ -f "$BACKEND_ENV" ]; then
                    sed -i '/^DEFAULT_DISTRO=/d' "$BACKEND_ENV" 2>/dev/null || sed -i.bak '/^DEFAULT_DISTRO=/d' "$BACKEND_ENV"
                fi
                echo "DEFAULT_DISTRO=$SELECTED_DISTRO" >> "$BACKEND_ENV"
                echo "💡 Дистрибутив '$SELECTED_DISTRO' сохранен в backend/.env"
                ;;
            4|*)
                echo "⚠️  Продолжаем без образов (песочницы будут недоступны)"
                echo "💡 Вы можете создать образы позже: cd scripts && ./create-astra-image.sh --vnc"
                ;;
        esac
    else
        echo "✅ Найдены следующие образы:"
        echo ""
        for i in "${!AVAILABLE_OPTIONS[@]}"; do
            echo "  $((i+1))) ${AVAILABLE_NAMES[$i]} (${AVAILABLE_OPTIONS[$i]})"
        done
        echo "  $((count + 1))) Продолжить без выбора"
        echo ""
        read -p "Выберите вариант (1-$((count + 1))): " choice
        echo ""
        
        if [ "$choice" -ge 1 ] && [ "$choice" -le $count ]; then
            SELECTED_IMAGE="${AVAILABLE_OPTIONS[$((choice-1))]}"
            SELECTED_NAME="${AVAILABLE_NAMES[$((choice-1))]}"
            echo "✅ Выбран образ: $SELECTED_NAME"
            echo "   $SELECTED_IMAGE"
            
            # Определяем дистрибутив из выбранного образа
            if echo "$SELECTED_IMAGE" | grep -q "debian"; then
                SELECTED_DISTRO="debian"
            elif echo "$SELECTED_IMAGE" | grep -q "ubuntu"; then
                SELECTED_DISTRO="ubuntu"
            elif echo "$SELECTED_IMAGE" | grep -q "astra"; then
                SELECTED_DISTRO="astra"
            fi
            
            # Сохраняем выбранный дистрибутив в .env файл для backend
            if [ -n "$SELECTED_DISTRO" ]; then
                BACKEND_ENV="$PROJECT_ROOT/backend/.env"
                # Удаляем старую строку DEFAULT_DISTRO если есть
                if [ -f "$BACKEND_ENV" ]; then
                    sed -i '/^DEFAULT_DISTRO=/d' "$BACKEND_ENV" 2>/dev/null || sed -i.bak '/^DEFAULT_DISTRO=/d' "$BACKEND_ENV"
                fi
                # Добавляем новую строку
                echo "DEFAULT_DISTRO=$SELECTED_DISTRO" >> "$BACKEND_ENV"
                echo "💡 Дистрибутив '$SELECTED_DISTRO' сохранен в backend/.env"
            fi
        else
            echo "📦 Продолжаем без выбора (будет использован дистрибутив по умолчанию)"
        fi
    fi
    echo ""
}

# Выбор образа
SELECTED_DISTRO=""  # Инициализируем переменную для выбранного дистрибутива
if [ -n "$CONTAINER_CMD" ]; then
    select_image
    # Если была выбрана дистрибутив, сохраняем для использования ниже
    if [ -n "$SELECTED_DISTRO" ]; then
        export SELECTED_DISTRO
    fi
else
    echo "⚠️  Docker/Podman не найден, пропускаем выбор образа"
    echo "💡 Установите Docker Desktop для Windows для работы с контейнерами"
    echo ""
fi

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

# Остановка старого Backend (если запущен) для применения новой конфигурации
echo "🧹 Очистка старых процессов..."
pkill -f 'python.*run.py' 2>/dev/null || true
pkill -f 'uvicorn.*main:app' 2>/dev/null || true
pkill -f 'react-scripts start' 2>/dev/null || true
sleep 2
echo "✅ Очистка завершена"
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
