#!/bin/bash
# Скрипт запуска Linux Training Simulator для WSL

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR" && pwd)"

# Парсинг аргументов
FORCE_UPDATE_LLM_IP=false
LM_STUDIO_IP_MANUAL=""
for arg in "$@"; do
    case $arg in
        --update-llm-ip|--force-llm-ip)
            FORCE_UPDATE_LLM_IP=true
            shift
            ;;
        --lm-studio-ip)
            shift
            LM_STUDIO_IP_MANUAL="$1"
            if [ -z "$LM_STUDIO_IP_MANUAL" ]; then
                echo "Ошибка: --lm-studio-ip требует IP адрес"
                exit 1
            fi
            shift
            ;;
        -h|--help)
            echo "Использование: $0 [опции]"
            echo ""
            echo "Опции:"
            echo "  --update-llm-ip, --force-llm-ip  Принудительно обновить IP адрес для LM Studio в .env"
            echo "  --lm-studio-ip IP               Указать IP адрес LM Studio вручную (например, 192.168.56.1)"
            echo "  -h, --help                      Показать эту справку"
            exit 0
            ;;
        *)
            ;;
    esac
done

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

# Улучшенное определение IP Windows хоста (работает даже при раздаче интернета с мобильного)
WINDOWS_HOST_IP=""

# Метод 1: Через /etc/resolv.conf (nameserver) - основной метод для WSL2
if [ -z "$WINDOWS_HOST_IP" ]; then
    WINDOWS_HOST_IP=$(cat /etc/resolv.conf 2>/dev/null | grep nameserver | awk '{print $2}' | head -1 | grep -v '^127\.' || echo "")
fi

# Метод 2: Через ip route (шлюз по умолчанию)
if [ -z "$WINDOWS_HOST_IP" ] || [ "$WINDOWS_HOST_IP" = "127.0.0.1" ]; then
    WINDOWS_HOST_IP=$(ip route show default 2>/dev/null | awk '/default/ {print $3}' | head -1 | grep -v '^127\.' || echo "")
fi

# Метод 3: Через hostname -I и вычисление IP Windows (для разных сетевых конфигураций)
if [ -z "$WINDOWS_HOST_IP" ] || [ "$WINDOWS_HOST_IP" = "127.0.0.1" ]; then
    if [ -n "$WSL_IP" ]; then
        # Пробуем разные варианты на основе IP WSL
        WSL_IP_PARTS=($(echo "$WSL_IP" | tr '.' ' '))
        if [ ${#WSL_IP_PARTS[@]} -eq 4 ]; then
            # Вариант 1: .1 в конце (часто используется)
            CANDIDATE1="${WSL_IP_PARTS[0]}.${WSL_IP_PARTS[1]}.${WSL_IP_PARTS[2]}.1"
            # Вариант 2: .254 в конце (WSL2 часто использует)
            CANDIDATE2="${WSL_IP_PARTS[0]}.${WSL_IP_PARTS[1]}.${WSL_IP_PARTS[2]}.254"
            # Проверяем доступность через ping
            if ping -c 1 -W 1 "$CANDIDATE1" &>/dev/null; then
                WINDOWS_HOST_IP="$CANDIDATE1"
            elif ping -c 1 -W 1 "$CANDIDATE2" &>/dev/null; then
                WINDOWS_HOST_IP="$CANDIDATE2"
            else
                # Используем первый вариант по умолчанию
                WINDOWS_HOST_IP="$CANDIDATE1"
            fi
        fi
    fi
fi

# Метод 4: Через ip addr show и поиск шлюза в той же подсети
if [ -z "$WINDOWS_HOST_IP" ] || [ "$WINDOWS_HOST_IP" = "127.0.0.1" ]; then
    # Получаем все IP адреса и ищем шлюз
    GATEWAY_IP=$(ip route | grep default | awk '{print $3}' | head -1 | grep -v '^127\.' || echo "")
    if [ -n "$GATEWAY_IP" ]; then
        WINDOWS_HOST_IP="$GATEWAY_IP"
    fi
fi

# Если все еще не определили, пробуем получить через PowerShell (если доступен)
if [ -z "$WINDOWS_HOST_IP" ] || [ "$WINDOWS_HOST_IP" = "127.0.0.1" ]; then
    if command -v powershell.exe &>/dev/null; then
        PS_IP=$(powershell.exe -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*'}).IPAddress" 2>/dev/null | head -1 | tr -d '\r' || echo "")
        if [ -n "$PS_IP" ] && [ "$PS_IP" != "127.0.0.1" ]; then
            WINDOWS_HOST_IP="$PS_IP"
        fi
    fi
fi

# Если не удалось получить IP, пробуем альтернативные методы для WSL IP
if [ -z "$WSL_IP" ]; then
    WSL_IP=$(ip addr show | grep -oP 'inet \K[\d.]+' | grep -v '127.0.0.1' | head -1 || echo "")
fi

# Финальная проверка: если IP все еще не определен, используем localhost как fallback
if [ -z "$WINDOWS_HOST_IP" ] || [ "$WINDOWS_HOST_IP" = "127.0.0.1" ]; then
    echo "   ⚠️  Не удалось определить IP Windows хоста, используем localhost"
    WINDOWS_HOST_IP="127.0.0.1"
fi

echo "   WSL IP: $WSL_IP"
echo "   Windows Host IP: $WINDOWS_HOST_IP"
echo ""
# -----------------------------
# Автоматическое обновление IP адреса для LM Studio в .env
# -----------------------------
BACKEND_ENV="$PROJECT_ROOT/backend/.env"

# Функция: получить значение ключа из .env (удаляет кавычки и пробелы)
get_env_value() {
    local key="$1"
    local file="$2"
    if [ -f "$file" ]; then
        # ищем ключ, игнорируем комментарии, берём первое совпадение
        local val
        val=$(grep -E "^${key}=" "$file" 2>/dev/null | tail -1 | cut -d'=' -f2- | sed 's/^["'\'']//; s/["'\'']$//' | xargs 2>/dev/null || echo "")
        echo "$val"
    else
        echo ""
    fi
}

# Читаем порт LM Studio из backend/.env, если он задан
LM_STUDIO_PORT=$(get_env_value "LM_STUDIO_PORT" "$BACKEND_ENV")

# Если явно не задан, пытаемся извлечь порт из LLM_API_URL (если он там есть)
if [ -z "$LM_STUDIO_PORT" ]; then
    EXISTING_LLM_URL=$(get_env_value "LLM_API_URL" "$BACKEND_ENV")
    if [ -n "$EXISTING_LLM_URL" ]; then
        # попробуем разобрать http://ip:port[/...]
        # извлечем цифры порта
        LM_STUDIO_PORT=$(echo "$EXISTING_LLM_URL" | sed -n 's|.*:\([0-9]\+\)/.*|\1|p' || true)
        # если предыдущая команда ничего не вернула, пробуем без /v1
        if [ -z "$LM_STUDIO_PORT" ]; then
            LM_STUDIO_PORT=$(echo "$EXISTING_LLM_URL" | sed -n 's|.*:\([0-9]\+\)$|\1|p' || true)
        fi
    fi
fi

# По умолчанию используем порт 1235, если не удалось определить
LM_STUDIO_PORT=${LM_STUDIO_PORT:-1235}

echo "🔍 Используем порт LM Studio: $LM_STUDIO_PORT"

# Если IP указан вручную, используем его
if [ -n "$LM_STUDIO_IP_MANUAL" ]; then
    echo "🔍 Используется указанный вручную IP адрес LM Studio: ${LM_STUDIO_IP_MANUAL}"
    echo "🔍 Проверка доступности LM Studio на ${LM_STUDIO_IP_MANUAL}:${LM_STUDIO_PORT}..."
    if curl -s --connect-timeout 3 --max-time 5 "http://${LM_STUDIO_IP_MANUAL}:${LM_STUDIO_PORT}/v1/models" >/dev/null 2>&1; then
        echo "   ✅ LM Studio доступен на ${LM_STUDIO_IP_MANUAL}:${LM_STUDIO_PORT}"
        LM_STUDIO_IP="$LM_STUDIO_IP_MANUAL"
    else
        echo "   ⚠️  LM Studio недоступен на ${LM_STUDIO_IP_MANUAL}:${LM_STUDIO_PORT}, но продолжаем с указанным IP"
        LM_STUDIO_IP="$LM_STUDIO_IP_MANUAL"
    fi
fi

# Сначала проверяем localhost (127.0.0.1) - это часто работает в WSL2
if [ -z "$LM_STUDIO_IP" ]; then
    echo "🔍 Проверка доступности LM Studio на localhost:${LM_STUDIO_PORT}..."
    if curl -s --connect-timeout 2 --max-time 3 "http://127.0.0.1:${LM_STUDIO_PORT}/v1/models" >/dev/null 2>&1; then
        echo "   ✅ LM Studio доступен на localhost:${LM_STUDIO_PORT}"
        LM_STUDIO_IP="127.0.0.1"
    fi
fi

# Проверяем доступность LM Studio по текущему IP (если не указан вручную и localhost не работает)
if [ -z "$LM_STUDIO_IP" ] && [ -n "$WINDOWS_HOST_IP" ] && [ "$WINDOWS_HOST_IP" != "127.0.0.1" ]; then
    echo "🔍 Проверка доступности LM Studio на ${WINDOWS_HOST_IP}:${LM_STUDIO_PORT}..."
    if timeout 2 bash -c "echo > /dev/tcp/${WINDOWS_HOST_IP}/${LM_STUDIO_PORT}" 2>/dev/null || curl -s --connect-timeout 2 "http://${WINDOWS_HOST_IP}:${LM_STUDIO_PORT}/v1/models" >/dev/null 2>&1; then
        echo "   ✅ LM Studio доступен на ${WINDOWS_HOST_IP}:${LM_STUDIO_PORT}"
        LM_STUDIO_IP="$WINDOWS_HOST_IP"
    else
        echo "   ⚠️  LM Studio недоступен на ${WINDOWS_HOST_IP}:${LM_STUDIO_PORT}, пробуем другие варианты..."
        # Пробуем другие возможные IP адреса (на тех же хост-узлах), сохраняя порт
        if [ -n "$WSL_IP" ]; then
            WSL_IP_PARTS=($(echo "$WSL_IP" | tr '.' ' '))
            if [ ${#WSL_IP_PARTS[@]} -eq 4 ]; then
                CANDIDATES=(
                    "${WSL_IP_PARTS[0]}.${WSL_IP_PARTS[1]}.${WSL_IP_PARTS[2]}.1"
                    "${WSL_IP_PARTS[0]}.${WSL_IP_PARTS[1]}.${WSL_IP_PARTS[2]}.254"
                    "${WSL_IP_PARTS[0]}.${WSL_IP_PARTS[1]}.${WSL_IP_PARTS[2]}.2"
                    "192.168.56.1"  # Часто используемый IP для VirtualBox/VMware адаптеров
                    "10.0.2.2"      # Другой распространенный IP для виртуальных адаптеров
                )
                for CANDIDATE in "${CANDIDATES[@]}"; do
                    if timeout 2 bash -c "echo > /dev/tcp/${CANDIDATE}/${LM_STUDIO_PORT}" 2>/dev/null || curl -s --connect-timeout 2 "http://${CANDIDATE}:${LM_STUDIO_PORT}/v1/models" >/dev/null 2>&1; then
                        echo "   ✅ LM Studio найден на ${CANDIDATE}:${LM_STUDIO_PORT}"
                        LM_STUDIO_IP="$CANDIDATE"
                        break
                    fi
                done
            fi
        fi
        # Дополнительная проверка: пробуем распространенные IP адреса для виртуальных адаптеров
        if [ -z "$LM_STUDIO_IP" ]; then
            echo "   🔍 Проверяем распространенные IP адреса для виртуальных адаптеров..."
            COMMON_IPS=("192.168.56.1" "192.168.137.1" "192.168.0.1" "10.0.2.2")
            for COMMON_IP in "${COMMON_IPS[@]}"; do
                # Проверяем доступность через curl с явным выводом ошибок в режиме отладки
                if curl -s --connect-timeout 3 --max-time 5 "http://${COMMON_IP}:${LM_STUDIO_PORT}/v1/models" >/dev/null 2>&1; then
                    echo "   ✅ LM Studio найден на ${COMMON_IP}:${LM_STUDIO_PORT}"
                    LM_STUDIO_IP="$COMMON_IP"
                    break
                fi
                # Дополнительная проверка через TCP соединение
                if timeout 3 bash -c "echo > /dev/tcp/${COMMON_IP}/${LM_STUDIO_PORT}" 2>/dev/null; then
                    # Если TCP соединение успешно, пробуем еще раз через HTTP
                    if curl -s --connect-timeout 2 "http://${COMMON_IP}:${LM_STUDIO_PORT}/v1/models" >/dev/null 2>&1; then
                        echo "   ✅ LM Studio найден на ${COMMON_IP}:${LM_STUDIO_PORT}"
                        LM_STUDIO_IP="$COMMON_IP"
                        break
                    fi
                fi
            done
        fi
        # Если все еще не нашли, пробуем получить IP адреса Windows через PowerShell
        if [ -z "$LM_STUDIO_IP" ] && command -v powershell.exe &>/dev/null; then
            echo "   🔍 Пробуем определить IP адрес LM Studio через PowerShell..."
            # Получаем все IP адреса Windows, исключая loopback и link-local
            PS_IPS=$(powershell.exe -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object {\$_.IPAddress -notlike '127.*' -and \$_.IPAddress -notlike '169.254.*'} | Select-Object -ExpandProperty IPAddress" 2>/dev/null | tr -d '\r' | tr ' ' '\n' | grep -v '^$' || echo "")
            if [ -n "$PS_IPS" ]; then
                # Используем for loop вместо while, чтобы переменная сохранилась
                for PS_IP in $PS_IPS; do
                    [ -z "$PS_IP" ] && continue
                    [ -n "$LM_STUDIO_IP" ] && break  # Уже нашли
                    if timeout 2 bash -c "echo > /dev/tcp/${PS_IP}/${LM_STUDIO_PORT}" 2>/dev/null || curl -s --connect-timeout 2 "http://${PS_IP}:${LM_STUDIO_PORT}/v1/models" >/dev/null 2>&1; then
                        echo "   ✅ LM Studio найден на ${PS_IP}:${LM_STUDIO_PORT}"
                        LM_STUDIO_IP="$PS_IP"
                        break
                    fi
                done
            fi
        fi
        # Если не нашли, используем исходный IP
        if [ -z "$LM_STUDIO_IP" ]; then
            LM_STUDIO_IP="$WINDOWS_HOST_IP"
            echo "   ⚠️  LM Studio недоступен по проверке на ${WINDOWS_HOST_IP}:${LM_STUDIO_PORT}"
            echo "   💡 Возможно, требуется настройка port forwarding в Windows"
            echo "   💡 Выполните в PowerShell (от имени администратора):"
            echo "      PowerShell -ExecutionPolicy Bypass -File scripts/setup-lm-studio-port-forwarding.ps1 -Port ${LM_STUDIO_PORT}"
            echo "   ℹ️  Продолжаем с IP $WINDOWS_HOST_IP (может не работать без port forwarding)"
        fi
    fi
else
    # Если IP не определен, используем localhost (это часто работает в WSL2)
    if [ -z "$LM_STUDIO_IP" ]; then
    LM_STUDIO_IP="127.0.0.1"
        echo "   ℹ️  Используем localhost для LM Studio (127.0.0.1)"
        echo "   💡 Если это не работает, укажите IP вручную: --lm-studio-ip <IP>"
    fi
fi

# Формируем ожидаемый URL
EXPECTED_LLM_URL="http://${LM_STUDIO_IP}:${LM_STUDIO_PORT}/v1"

# Обновляем (или создаём) запись в backend/.env
if [ -f "$BACKEND_ENV" ]; then
    CURRENT_LLM_URL=$(get_env_value "LLM_API_URL" "$BACKEND_ENV")
    CURRENT_PORT_IN_ENV=$(get_env_value "LM_STUDIO_PORT" "$BACKEND_ENV")
    # Обновляем LLM_API_URL и LM_STUDIO_PORT при необходимости
    if [ "$FORCE_UPDATE_LLM_IP" = true ] || [ -z "$CURRENT_LLM_URL" ] || echo "$CURRENT_LLM_URL" | grep -qE "(localhost|127\.0\.0\.1)"; then
        if [ "$FORCE_UPDATE_LLM_IP" = true ]; then
            echo "🔧 Принудительное обновление LLM_API_URL и LM_STUDIO_PORT в backend/.env..."
        else
            echo "🔧 Обновление LLM_API_URL и LM_STUDIO_PORT в backend/.env..."
        fi
        # Удаляем старые строки если есть
        sed -i '/^LLM_API_URL=/d' "$BACKEND_ENV" 2>/dev/null || sed -i.bak '/^LLM_API_URL=/d' "$BACKEND_ENV"
        sed -i '/^LM_STUDIO_PORT=/d' "$BACKEND_ENV" 2>/dev/null || sed -i.bak '/^LM_STUDIO_PORT=/d' "$BACKEND_ENV"
        # Добавляем новые строки
        echo "LLM_API_URL=$EXPECTED_LLM_URL" >> "$BACKEND_ENV"
        echo "LM_STUDIO_PORT=$LM_STUDIO_PORT" >> "$BACKEND_ENV"
        echo "   ✅ LLM_API_URL и LM_STUDIO_PORT обновлены: $EXPECTED_LLM_URL, port $LM_STUDIO_PORT"
    else
        echo "   ℹ️  LLM_API_URL уже настроен: $CURRENT_LLM_URL"
        if [ -z "$CURRENT_PORT_IN_ENV" ]; then
            echo "   ℹ️  LM_STUDIO_PORT не задан в .env — добавим порт $LM_STUDIO_PORT"
            echo "LM_STUDIO_PORT=$LM_STUDIO_PORT" >> "$BACKEND_ENV"
        fi
        echo "   💡 Для принудительного обновления используйте: $0 --update-llm-ip"
    fi
else
    # Создаем .env файл если его нет
    echo "🔧 Создание backend/.env с настройками LLM..."
    mkdir -p "$PROJECT_ROOT/backend"
    cat > "$BACKEND_ENV" << EOF
# LLM настройки для генерации персональных миссий
LLM_HINTS_ENABLED=true
LLM_PROVIDER=lm_studio
LLM_API_URL=${EXPECTED_LLM_URL}
LLM_MODEL=mistralai/ministral-3-3b
LM_STUDIO_PORT=${LM_STUDIO_PORT}
EOF
    echo "   ✅ Создан backend/.env с LLM_API_URL: ${EXPECTED_LLM_URL} и LM_STUDIO_PORT=${LM_STUDIO_PORT}"
fi
echo ""
# -----------------------------
# Конец блока LM Studio
# -----------------------------
echo ""

# Формируем список дополнительных origins для CORS (будет обновлен после определения порта frontend)
# Пока используем порт 3000 по умолчанию, потом обновим
ADDITIONAL_ORIGINS_LIST=""

# Остановка старого Backend (если запущен) для применения новой конфигурации
echo "🧹 Очистка старых процессов..."
pkill -f 'python.*run.py' 2>/dev/null || true
pkill -f 'uvicorn.*main:app' 2>/dev/null || true
pkill -f 'react-scripts start' 2>/dev/null || true
sleep 3
echo "✅ Очистка завершена"
echo ""

# Определение свободного порта для Backend
echo "🔍 Проверка доступности портов для Backend..."
BACKEND_PORT=8000

# Функция проверки доступности порта
check_port() {
    local port=$1
    # Проверяем через несколько методов
    if timeout 1 bash -c "echo > /dev/tcp/127.0.0.1/$port" 2>/dev/null; then
        return 1  # Порт занят
    fi
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        return 1  # Порт занят
    fi
    if ss -tuln 2>/dev/null | grep -q ":$port "; then
        return 1  # Порт занят
    fi
    # Дополнительная проверка через lsof
    if command -v lsof &>/dev/null; then
        if lsof -ti:$port &>/dev/null; then
            return 1  # Порт занят
        fi
    fi
    return 0  # Порт свободен
}

if ! check_port $BACKEND_PORT; then
    echo "   ⚠️  Порт $BACKEND_PORT занят, пробуем 8001..."
    BACKEND_PORT=8001
    if ! check_port $BACKEND_PORT; then
        echo "   ⚠️  Порт 8001 тоже занят, пробуем 8002..."
        BACKEND_PORT=8002
        if ! check_port $BACKEND_PORT; then
            echo "   ❌ Порты 8000, 8001, 8002 заняты. Освободите один из них или укажите другой порт."
            exit 1
        fi
    fi
fi
echo "   ✅ Используем порт: $BACKEND_PORT"
echo ""

# Запуск Backend
echo "🚀 Запуск Backend на порту $BACKEND_PORT..."
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено"
    echo "💡 Запустите: ./scripts/quickstart-wsl.sh"
    exit 1
fi

source venv/bin/activate

# Устанавливаем переменную окружения для дополнительных origins и порта
if [ -n "$ADDITIONAL_ORIGINS_LIST" ]; then
    export ADDITIONAL_ORIGINS="$ADDITIONAL_ORIGINS_LIST"
    echo "   Настроены дополнительные CORS origins: $ADDITIONAL_ORIGINS_LIST"
fi
export API_PORT=$BACKEND_PORT
echo "   Backend будет запущен на порту: $BACKEND_PORT"

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
echo "⏳ Ожидание запуска Backend на порту $BACKEND_PORT..."
BACKEND_READY=false
for i in {1..40}; do
    # Проверяем, что процесс еще работает
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Процесс backend завершился. Проверьте логи: tail -f backend.log"
        echo "   Последние строки лога:"
        tail -20 backend.log 2>/dev/null || echo "   Лог недоступен"
        exit 1
    fi
    # Проверяем доступность API
    if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null 2>&1 || curl -s "http://localhost:$BACKEND_PORT/api/v1/routes" > /dev/null 2>&1; then
        echo "✅ Backend готов на порту $BACKEND_PORT"
        BACKEND_READY=true
        break
    fi
    if [ $i -eq 20 ]; then
        echo "   ⏳ Backend еще запускается... (попытка $i/40)"
    fi
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    echo "⚠️  Backend не отвечает на порту $BACKEND_PORT после 40 секунд"
    echo "   Проверьте логи: tail -f backend.log"
    echo "   Последние строки лога:"
    tail -30 backend.log 2>/dev/null || echo "   Лог недоступен"
    echo ""
    echo "   Попробуйте запустить backend вручную для диагностики:"
    echo "   cd backend && source venv/bin/activate && API_PORT=$BACKEND_PORT python run.py"
fi
echo ""

# Обновляем список дополнительных origins для CORS с правильным портом frontend
# (порт frontend будет определен ниже, но мы обновим origins после его определения)
# Пока оставляем пустым, обновим после определения FRONTEND_PORT

# Определение свободного порта для Frontend
echo "🔍 Проверка доступности портов для Frontend..."
FRONTEND_PORT=3000

if ! check_port $FRONTEND_PORT; then
    echo "   ⚠️  Порт $FRONTEND_PORT занят, пробуем 3001..."
    FRONTEND_PORT=3001
    if ! check_port $FRONTEND_PORT; then
        echo "   ⚠️  Порт 3001 тоже занят, пробуем 3002..."
        FRONTEND_PORT=3002
        if ! check_port $FRONTEND_PORT; then
            echo "   ❌ Порты 3000, 3001, 3002 заняты. Освободите один из них или укажите другой порт."
            exit 1
        fi
    fi
fi
echo "   ✅ Используем порт: $FRONTEND_PORT"
echo ""

# Обновляем список дополнительных origins для CORS с правильным портом frontend
if [ -n "$WSL_IP" ]; then
    ADDITIONAL_ORIGINS_LIST="http://${WSL_IP}:${FRONTEND_PORT}"
fi
if [ -n "$WINDOWS_HOST_IP" ] && [ "$WINDOWS_HOST_IP" != "$WSL_IP" ]; then
    if [ -n "$ADDITIONAL_ORIGINS_LIST" ]; then
        ADDITIONAL_ORIGINS_LIST="${ADDITIONAL_ORIGINS_LIST},http://${WINDOWS_HOST_IP}:${FRONTEND_PORT}"
    else
        ADDITIONAL_ORIGINS_LIST="http://${WINDOWS_HOST_IP}:${FRONTEND_PORT}"
    fi
fi

# Обновляем переменную окружения для backend с правильными origins
if [ -n "$ADDITIONAL_ORIGINS_LIST" ]; then
    export ADDITIONAL_ORIGINS="$ADDITIONAL_ORIGINS_LIST"
    echo "   Обновлены дополнительные CORS origins: $ADDITIONAL_ORIGINS_LIST"
    echo ""
fi

# Запуск Frontend
echo "🌐 Запуск Frontend на порту $FRONTEND_PORT..."
cd "$PROJECT_ROOT/frontend/web"
if [ ! -d "node_modules" ]; then
    echo "❌ node_modules не найдены"
    echo "💡 Запустите: cd frontend/web && npm install"
    exit 1
fi

# Создаем .env.local файл для frontend с портом backend и frontend
cat > .env.local << EOF
REACT_APP_API_PORT=$BACKEND_PORT
PORT=$FRONTEND_PORT
EOF
echo "   Создан .env.local с REACT_APP_API_PORT=$BACKEND_PORT и PORT=$FRONTEND_PORT"

# Обновляем setupProxy.js для использования правильного порта
PROXY_FILE="src/setupProxy.js"
if [ -f "$PROXY_FILE" ]; then
    # Создаем резервную копию
    cp "$PROXY_FILE" "${PROXY_FILE}.bak" 2>/dev/null || true
    # Обновляем порт в setupProxy.js
    sed -i "s|target: 'http://localhost:8000'|target: 'http://localhost:$BACKEND_PORT'|g" "$PROXY_FILE"
    sed -i "s|target: \"http://localhost:8000\"|target: \"http://localhost:$BACKEND_PORT\"|g" "$PROXY_FILE"
    echo "   Обновлен setupProxy.js для использования порта $BACKEND_PORT"
fi

# Настраиваем frontend на прослушивание всех интерфейсов (0.0.0.0)
# Это позволит подключаться с других машин в локальной сети
BROWSER=none PORT=$FRONTEND_PORT REACT_APP_API_PORT=$BACKEND_PORT nohup npm start > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend запущен (PID родительского процесса: $FRONTEND_PID)"
echo "   Frontend слушает на всех интерфейсах (0.0.0.0:$FRONTEND_PORT)"
echo "   Frontend настроен на подключение к Backend на порту $BACKEND_PORT"

# Ждем немного и находим реальный PID процесса react-scripts
sleep 3
REAL_FRONTEND_PID=$(pgrep -f 'react-scripts start' | head -1)
if [ -n "$REAL_FRONTEND_PID" ]; then
    FRONTEND_PID=$REAL_FRONTEND_PID
    echo "   Реальный PID процесса: $FRONTEND_PID"
fi
cd "$PROJECT_ROOT"

# Ожидание запуска Frontend
echo "⏳ Ожидание запуска Frontend на порту $FRONTEND_PORT..."
FRONTEND_READY=false
for i in {1..60}; do
    # Проверяем, что процесс еще работает
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Процесс frontend завершился. Проверьте логи: tail -f frontend.log"
        echo "   Последние строки лога:"
        tail -20 frontend.log 2>/dev/null || echo "   Лог недоступен"
        exit 1
    fi
    # Проверяем доступность frontend
    if curl -s "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        echo "✅ Frontend готов на порту $FRONTEND_PORT"
        FRONTEND_READY=true
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ⏳ Frontend еще запускается... (попытка $i/60)"
    fi
    sleep 1
done

if [ "$FRONTEND_READY" = false ]; then
    echo "⚠️  Frontend не отвечает на порту $FRONTEND_PORT после 60 секунд"
    echo "   Проверьте логи: tail -f frontend.log"
    echo "   Последние строки лога:"
    tail -30 frontend.log 2>/dev/null || echo "   Лог недоступен"
    echo ""
    echo "   Попробуйте запустить frontend вручную для диагностики:"
    echo "   cd frontend/web && PORT=$FRONTEND_PORT REACT_APP_API_PORT=$BACKEND_PORT npm start"
fi
echo ""

# Диагностика сетевых подключений
echo "🔍 Диагностика сетевых подключений..."
echo ""

# Проверка прослушивания портов
echo "   Проверка портов:"
if command -v netstat &> /dev/null; then
    BACKEND_LISTENING=$(netstat -tuln 2>/dev/null | grep -E ":($FRONTEND_PORT|$BACKEND_PORT)" | grep "0.0.0.0" || echo "")
    if [ -n "$BACKEND_LISTENING" ]; then
        echo "   ✅ Порты слушают на 0.0.0.0:"
        echo "$BACKEND_LISTENING" | while read line; do
            echo "      $line"
        done
    else
        echo "   ⚠️  Порты могут не слушать на всех интерфейсах"
        echo "   💡 Проверьте: netstat -tuln | grep -E ':($FRONTEND_PORT|$BACKEND_PORT)'"
    fi
elif command -v ss &> /dev/null; then
    BACKEND_LISTENING=$(ss -tuln 2>/dev/null | grep -E ":($FRONTEND_PORT|$BACKEND_PORT)" | grep "0.0.0.0" || echo "")
    if [ -n "$BACKEND_LISTENING" ]; then
        echo "   ✅ Порты слушают на 0.0.0.0:"
        echo "$BACKEND_LISTENING" | while read line; do
            echo "      $line"
        done
    else
        echo "   ⚠️  Порты могут не слушать на всех интерфейсах"
        echo "   💡 Проверьте: ss -tuln | grep -E ':($FRONTEND_PORT|$BACKEND_PORT)'"
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
echo "   Frontend: http://localhost:$FRONTEND_PORT"
echo "   Backend:  http://localhost:$BACKEND_PORT"
echo "   API Docs: http://localhost:$BACKEND_PORT/docs"
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
    echo "   Frontend: http://${WINDOWS_HOST_IP_FOR_DISPLAY}:$FRONTEND_PORT"
    echo "   Backend:  http://${WINDOWS_HOST_IP_FOR_DISPLAY}:$BACKEND_PORT"
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
if [ "$LM_STUDIO_IP" = "$WINDOWS_HOST_IP" ] && [ -n "$WINDOWS_HOST_IP" ] && [ "$WINDOWS_HOST_IP" != "127.0.0.1" ]; then
    echo "🤖 Настройка LM Studio для работы из WSL:"
    echo "   Если LM Studio недоступен из WSL, настройте port forwarding:"
    echo "   PowerShell -ExecutionPolicy Bypass -File scripts/setup-lm-studio-port-forwarding.ps1 -Port ${LM_STUDIO_PORT}"
    echo "   (требуются права администратора)"
    echo ""
fi

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

