#!/bin/bash
# Entrypoint script for astra-vnc container
# Based on the original from shinbatsu/astra-ui-vnc-container

# Настройка русского языка
export LANG=ru_RU.UTF-8
export LANGUAGE=ru_RU:ru
export LC_ALL=ru_RU.UTF-8

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
if command -v websockify &> /dev/null; then
    WEBSOCKIFY_CMD="websockify"
elif [ -f "/opt/noVNC/utils/websockify/run" ]; then
    WEBSOCKIFY_CMD="/opt/noVNC/utils/websockify/run"
elif [ -f "/opt/noVNC/utils/websockify.py" ]; then
    WEBSOCKIFY_CMD="python3 /opt/noVNC/utils/websockify.py"
fi

if [ -n "$WEBSOCKIFY_CMD" ]; then
    echo "Запуск websockify..." >&2
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
fi

# Start fly window manager
export DISPLAY=:1
fly-wm > /dev/null 2>&1 &
FLY_PID=$!

# Wait for all processes
wait

