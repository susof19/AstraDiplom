#!/bin/bash
# Скрипт автоматического запуска TigerVNC и noVNC в контейнере

set -e

echo "🚀 Запуск VNC сервера для Astra Linux Training Simulator..."

# Переменные окружения с значениями по умолчанию
VNC_PORT=${VNC_PORT:-5900}
NOVNC_PORT=${NOVNC_PORT:-6080}
VNC_RESOLUTION=${VNC_RESOLUTION:-1280x720}
VNC_DEPTH=${VNC_DEPTH:-24}
DISPLAY=${DISPLAY:-:0}
USER=${USER:-astrauser}

# Функция очистки при завершении
cleanup() {
    echo "🛑 Остановка VNC сервера..."
    if [ -n "$VNC_PID" ]; then
        kill $VNC_PID 2>/dev/null || true
    fi
    if [ -n "$NOVNC_PID" ]; then
        kill $NOVNC_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT TERM INT

# Ожидание готовности системы
sleep 2

# Очистка старых lock-файлов
rm -rf /tmp/.X*-lock /tmp/.X11-unix 2>/dev/null || true
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

# Запуск VNC сервера
echo "📺 Запуск TigerVNC сервера на порту $VNC_PORT..."
echo "   Разрешение: $VNC_RESOLUTION"
echo "   Глубина цвета: $VNC_DEPTH бит"

# Переключаемся на пользователя astrauser для запуска VNC
su - astrauser -c "
    export DISPLAY=$DISPLAY
    export USER=astrauser
    export HOME=/home/astrauser
    
    # Убиваем старые процессы VNC если есть
    vncserver -kill $DISPLAY 2>/dev/null || true
    
    # Запускаем VNC сервер
    vncserver $DISPLAY \
        -geometry $VNC_RESOLUTION \
        -depth $VNC_DEPTH \
        -localhost no \
        -SecurityTypes None \
        -AlwaysShared \
        -AcceptSetDesktopSize \
        -xstartup /home/astrauser/.vnc/xstartup \
        2>&1 | tee /tmp/vnc.log
" &

VNC_PID=$!

# Ожидание запуска VNC сервера
echo "⏳ Ожидание запуска VNC сервера..."
for i in {1..30}; do
    if netstat -tuln | grep -q ":$VNC_PORT "; then
        echo "✅ VNC сервер запущен на порту $VNC_PORT"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Не удалось запустить VNC сервер"
        cat /tmp/vnc.log 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Запуск noVNC (websockify)
echo "🌐 Запуск noVNC на порту $NOVNC_PORT..."
/opt/noVNC/utils/novnc_proxy \
    --vnc localhost:$VNC_PORT \
    --listen $NOVNC_PORT \
    --web /opt/noVNC \
    2>&1 | tee /tmp/novnc.log &

NOVNC_PID=$!

# Ожидание запуска noVNC
echo "⏳ Ожидание запуска noVNC..."
for i in {1..30}; do
    if netstat -tuln | grep -q ":$NOVNC_PORT "; then
        echo "✅ noVNC запущен на порту $NOVNC_PORT"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Не удалось запустить noVNC"
        cat /tmp/novnc.log 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

echo ""
echo "✨ VNC сервер успешно запущен!"
echo ""
echo "📋 Информация о подключении:"
echo "   VNC порт: $VNC_PORT"
echo "   noVNC порт: $NOVNC_PORT"
echo "   Пользователь: astrauser"
echo "   Пароль: astra123"
echo ""
echo "🌐 Для подключения через браузер:"
echo "   http://localhost:$NOVNC_PORT/vnc.html"
echo ""

# Держим скрипт запущенным
wait $VNC_PID $NOVNC_PID

