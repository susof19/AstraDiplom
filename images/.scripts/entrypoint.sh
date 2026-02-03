#!/bin/bash
# Entrypoint script for astra-vnc container
# Based on the original from shinbatsu/astra-ui-vnc-container

# Настройка русского языка (проверяем наличие локали перед установкой)
if locale -a | grep -q "ru_RU.utf8"; then
    export LANG=ru_RU.UTF-8
    export LANGUAGE=ru_RU:ru
    export LC_ALL=ru_RU.UTF-8
else
    # Если локаль не найдена, используем C.UTF-8 (универсальная)
    export LANG=C.UTF-8
    export LANGUAGE=C
    export LC_ALL=C.UTF-8
    echo "Предупреждение: локаль ru_RU.UTF-8 не найдена, используется C.UTF-8" >&2
fi

# Start Xvfb
Xvfb :1 -screen 0 1024x768x24 > /dev/null 2>&1 &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Start x11vnc
x11vnc -display :1 -nopw -listen localhost -xkb -forever -shared -rfbport 5900 > /dev/null 2>&1 &
X11VNC_PID=$!

# Wait for x11vnc to start
sleep 2

# Start websockify for noVNC
# Проверяем разные возможные пути к websockify
WEBSOCKIFY_CMD=""
WEBSOCKIFY_PATH=""

# Проверяем в порядке приоритета
if command -v websockify &> /dev/null; then
    WEBSOCKIFY_CMD="websockify"
    WEBSOCKIFY_PATH=$(command -v websockify)
elif [ -f "/usr/local/bin/websockify" ] && [ -x "/usr/local/bin/websockify" ]; then
    WEBSOCKIFY_CMD="/usr/local/bin/websockify"
    WEBSOCKIFY_PATH="/usr/local/bin/websockify"
elif [ -f "/opt/noVNC/utils/websockify/run" ] && [ -x "/opt/noVNC/utils/websockify/run" ]; then
    WEBSOCKIFY_CMD="/opt/noVNC/utils/websockify/run"
    WEBSOCKIFY_PATH="/opt/noVNC/utils/websockify/run"
elif [ -f "/opt/noVNC/utils/websockify/websockify.py" ]; then
    WEBSOCKIFY_CMD="python3 /opt/noVNC/utils/websockify/websockify.py"
    WEBSOCKIFY_PATH="/opt/noVNC/utils/websockify/websockify.py"
fi

if [ -n "$WEBSOCKIFY_CMD" ] && [ -n "$WEBSOCKIFY_PATH" ]; then
    echo "Запуск websockify из: $WEBSOCKIFY_PATH" >&2
    if [ -d "/opt/noVNC" ]; then
        # Используем /opt/noVNC как web директорию
        $WEBSOCKIFY_CMD --web=/opt/noVNC 80 localhost:5900 > /dev/null 2>&1 &
    else
        # Fallback на стандартный путь
        $WEBSOCKIFY_CMD 80 localhost:5900 > /dev/null 2>&1 &
    fi
    WEBSOCKIFY_PID=$!
    echo "websockify запущен (PID: $WEBSOCKIFY_PID)" >&2
else
    echo "ОШИБКА: websockify не найден" >&2
    echo "Проверка путей:" >&2
    echo "  - /usr/local/bin/websockify: $([ -f /usr/local/bin/websockify ] && echo 'существует' || echo 'не найден')" >&2
    echo "  - /opt/noVNC/utils/websockify/run: $([ -f /opt/noVNC/utils/websockify/run ] && echo 'существует' || echo 'не найден')" >&2
    echo "  - /opt/noVNC/utils/websockify/websockify.py: $([ -f /opt/noVNC/utils/websockify/websockify.py ] && echo 'существует' || echo 'не найден')" >&2
    if [ -d "/opt/noVNC/utils/websockify" ]; then
        echo "Содержимое /opt/noVNC/utils/websockify:" >&2
        ls -la /opt/noVNC/utils/websockify/ >&2
    fi
fi

# Start fly window manager
export DISPLAY=:1
fly-wm > /dev/null 2>&1 &
FLY_PID=$!

# Ждем завершения всех критических процессов
# apt-cache инициализация запущена в фоне и не блокирует
wait

