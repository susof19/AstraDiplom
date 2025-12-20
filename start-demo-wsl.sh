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

# Получение IP адресов для доступа из локальной сети
echo "🌐 Определение сетевых адресов..."
WSL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "")
WINDOWS_HOST_IP=$(cat /etc/resolv.conf 2>/dev/null | grep nameserver | awk '{print $2}' | head -1 || echo "")

# Если не удалось получить IP, пробуем альтернативные методы
if [ -z "$WSL_IP" ]; then
    WSL_IP=$(ip addr show | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0.1' | head -1 || echo "")
fi

if [ -z "$WINDOWS_HOST_IP" ]; then
    WINDOWS_HOST_IP=$(ip route show | grep -i default | awk '{print $3}' | head -1 || echo "")
fi

echo "   WSL IP: $WSL_IP"
echo "   Windows Host IP: $WINDOWS_HOST_IP"
echo ""

# Формируем список дополнительных origins для CORS
ADDITIONAL_ORIGINS_LIST=""
if [ -n "$WSL_IP" ]; then
    ADDITIONAL_ORIGINS_LIST="http://${WSL_IP}:3000"
fi
if [ -n "$WINDOWS_HOST_IP" ] && [ "$WINDOWS_HOST_IP" != "$WSL_IP" ]; then
    if [ -n "$ADDITIONAL_ORIGINS_LIST" ]; then
        ADDITIONAL_ORIGINS_LIST="${ADDITIONAL_ORIGINS_LIST},http://${WINDOWS_HOST_IP}:3000"
    else
        ADDITIONAL_ORIGINS_LIST="http://${WINDOWS_HOST_IP}:3000"
    fi
fi

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
cd "$PROJECT_ROOT"

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
    BACKEND_LISTENING=$(netstat -tuln 2>/dev/null | grep -E ":(3000|8000)" | grep "0.0.0.0" || echo "")
    if [ -n "$BACKEND_LISTENING" ]; then
        echo "   ✅ Порты слушают на 0.0.0.0:"
        echo "$BACKEND_LISTENING" | while read line; do
            echo "      $line"
        done
    else
        echo "   ⚠️  Порты могут не слушать на всех интерфейсах"
        echo "   💡 Проверьте: netstat -tuln | grep -E ':(3000|8000)'"
    fi
elif command -v ss &> /dev/null; then
    BACKEND_LISTENING=$(ss -tuln 2>/dev/null | grep -E ":(3000|8000)" | grep "0.0.0.0" || echo "")
    if [ -n "$BACKEND_LISTENING" ]; then
        echo "   ✅ Порты слушают на 0.0.0.0:"
        echo "$BACKEND_LISTENING" | while read line; do
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

# Получение IP адреса Windows хоста для отображения
WINDOWS_HOST_IP_FOR_DISPLAY=""
if [ -n "$WINDOWS_HOST_IP" ]; then
    WINDOWS_HOST_IP_FOR_DISPLAY="$WINDOWS_HOST_IP"
else
    # Пробуем получить через ipconfig в WSL
    WINDOWS_HOST_IP_FOR_DISPLAY=$(cat /etc/resolv.conf 2>/dev/null | grep nameserver | awk '{print $2}' | head -1 || echo "")
fi

# Проверка port forwarding (если доступен wsl.exe)
if command -v wsl.exe &> /dev/null 2>&1 || [ -n "$(which wsl.exe 2>/dev/null)" ]; then
    echo "   Проверка port forwarding в Windows..."
    echo "   💡 Для доступа из локальной сети выполните в PowerShell (от имени администратора):"
    echo "      PowerShell -ExecutionPolicy Bypass -File scripts/setup-wsl-port-forwarding.ps1"
    echo "   Или используйте mirrored networking mode (рекомендуется):"
    echo "      PowerShell -ExecutionPolicy Bypass -File scripts/setup-wsl-mirrored-networking.ps1"
    echo ""
fi

echo ""
echo "=================================================="
echo "✅ Демонстрация запущена!"
echo ""
echo "📋 Сервисы (локальный доступ):"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""

# Выводим информацию о доступе из локальной сети
echo "🌐 Доступ из локальной сети:"
echo ""
echo "⚠️  ВАЖНО: WSL2 требует настройки port forwarding для доступа из локальной сети!"
echo ""
echo "📋 Вариант 1 (Рекомендуется): Mirrored Networking Mode"
echo "   Выполните в PowerShell от имени администратора:"
echo "   PowerShell -ExecutionPolicy Bypass -File scripts/setup-wsl-mirrored-networking.ps1"
echo "   Затем перезапустите WSL: wsl --shutdown"
echo ""
echo "📋 Вариант 2: Port Forwarding"
echo "   Выполните в PowerShell от имени администратора:"
echo "   PowerShell -ExecutionPolicy Bypass -File scripts/setup-wsl-port-forwarding.ps1"
echo ""

# Получаем IP адрес Windows хоста для отображения
if [ -n "$WINDOWS_HOST_IP_FOR_DISPLAY" ]; then
    echo "💡 После настройки port forwarding используйте IP адрес Windows хоста:"
    echo "   Frontend: http://${WINDOWS_HOST_IP_FOR_DISPLAY}:3000"
    echo "   Backend:  http://${WINDOWS_HOST_IP_FOR_DISPLAY}:8000"
    echo ""
    echo "   Узнать IP адрес Windows хоста:"
    echo "   В PowerShell: ipconfig | findstr IPv4"
    echo "   Или в WSL: cat /etc/resolv.conf | grep nameserver | awk '{print \$2}'"
else
    echo "💡 После настройки port forwarding используйте IP адрес Windows хоста"
    echo "   Узнать IP адрес: ipconfig | findstr IPv4 (в PowerShell)"
fi
echo ""
echo "🔧 Дополнительно убедитесь, что:"
echo "   1. Windows Firewall разрешает подключения (скрипт настроит автоматически)"
echo "   2. Оба устройства в одной локальной сети"
echo "   3. Порты 3000 и 8000 не заняты другими приложениями"
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
