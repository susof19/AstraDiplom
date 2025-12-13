#!/bin/bash
# Не используем set -euo pipefail, чтобы скрипт не падал на незначительных ошибках
set +e

USER="sandboxuser"
HOME="/home/$USER"
export HOME

# Логирование для отладки
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

log "Запуск VNC сервера для пользователя $USER"

# Определяем команду VNC сервера
VNC_CMD=""
if command -v vncserver &>/dev/null; then
    VNC_CMD="vncserver"
elif command -v Xtigervnc &>/dev/null || command -v Xvnc &>/dev/null; then
    # Используем прямой запуск через Xvnc/Xtigervnc
    log "Используем прямой запуск Xvnc/Xtigervnc"
    VNC_CMD="direct"
else
    log "ОШИБКА: VNC сервер не найден"
    # Продолжаем работу, может быть установится позже
fi

# kill old sessions
log "Остановка старых VNC сессий..."
if [ -n "$VNC_CMD" ] && [ "$VNC_CMD" != "direct" ]; then
su - "$USER" -c "vncserver -kill :0" >/dev/null 2>&1 || true
    sleep 1
fi

# Очищаем старые PID файлы
rm -f "$HOME/.vnc/*:0.pid" 2>/dev/null || true
rm -f /tmp/.X0-lock 2>/dev/null || true
rm -f /tmp/.X11-unix/X0 2>/dev/null || true

# ensure passwd exists or create default
if [ ! -f "$HOME/.vnc/passwd" ]; then
  log "Создание VNC пароля..."
  mkdir -p "$HOME/.vnc" || true
  if command -v vncpasswd &>/dev/null; then
      su - "$USER" -c "echo 'sandbox123' | vncpasswd -f > ~/.vnc/passwd && chmod 600 ~/.vnc/passwd" 2>&1 || true
  elif command -v x11vnc &>/dev/null; then
      su - "$USER" -c "x11vnc -storepasswd sandbox123 ~/.vnc/passwd" 2>&1 || true
      chmod 600 "$HOME/.vnc/passwd" 2>/dev/null || true
  fi
fi

# start vncserver as the user
log "Запуск VNC сервера на дисплее :0..."
VNC_STARTED=false

# Создаем X сервер если его нет (для x11vnc)
if ! pgrep -f "X.*:0" > /dev/null 2>&1; then
    log "X сервер не найден, пытаемся запустить через Xvfb..."
    if command -v Xvfb &>/dev/null; then
        su - "$USER" -c "Xvfb :0 -screen 0 ${VNC_RESOLUTION:-1280x720}x${VNC_DEPTH:-24}" >/dev/null 2>&1 &
        sleep 2
    fi
fi

if [ -n "$VNC_CMD" ] && [ "$VNC_CMD" = "vncserver" ]; then
    # Попытка запуска через vncserver (tigervnc или tightvnc)
    log "Попытка запуска через vncserver..."
    # Убеждаемся, что xstartup исполняемый и правильный
    chmod +x "$HOME/.vnc/xstartup" 2>/dev/null || true
    # Запускаем vncserver с явным указанием разрешения и без localhost ограничения
    su - "$USER" -c "cd ~ && vncserver :0 -geometry ${VNC_RESOLUTION:-1280x720} -depth ${VNC_DEPTH:-24} -localhost no -SecurityTypes VncAuth" > /tmp/vnc-start.log 2>&1
    VNC_EXIT_CODE=$?
    if [ $VNC_EXIT_CODE -eq 0 ]; then
        VNC_STARTED=true
        log "vncserver запущен успешно"
        log "Ожидание запуска рабочего стола (10 секунд)..."
        sleep 10  # Даем время XFCE запуститься
    else
        log "vncserver вернул ошибку (код: $VNC_EXIT_CODE), проверяем логи..."
        cat /tmp/vnc-start.log >&2 || true
        
        # Попробуем альтернативный способ - запуск через Xvnc напрямую
        log "Пробуем альтернативный способ запуска..."
        if command -v Xtigervnc &>/dev/null; then
            log "Запуск через Xtigervnc напрямую..."
            su - "$USER" -c "cd ~ && Xtigervnc :0 -geometry ${VNC_RESOLUTION:-1280x720} -depth ${VNC_DEPTH:-24} -localhost no -SecurityTypes VncAuth -rfbauth ~/.vnc/passwd -xstartup ~/.vnc/xstartup" > /tmp/vnc-direct.log 2>&1 &
            sleep 10  # Даем время XFCE запуститься
        fi
    fi
elif command -v x11vnc &>/dev/null; then
    # Альтернатива: используем x11vnc если доступен
    log "Используем x11vnc как альтернативу..."
    su - "$USER" -c "x11vnc -display :0 -forever -usepw -rfbport 5900 -shared -bg -o /tmp/x11vnc.log" 2>&1
    sleep 2
fi

# Даем VNC серверу время на запуск
sleep 3

# wait for the X process to exist so supervisord treats this program as running
log "Ожидание процесса X сервера..."
for i in {1..15}; do
    PID=$(pgrep -f "Xtigervnc.*:0" 2>/dev/null || pgrep -f "Xvnc.*:0" 2>/dev/null || pgrep -f "vncserver.*:0" 2>/dev/null || true)
if [ -n "$PID" ]; then
        log "VNC сервер запущен (PID: $PID)"
        # Проверяем, что процесс действительно работает
        if ps -p "$PID" > /dev/null 2>&1; then
  # block on PID so supervisor keeps process alive
            log "Отслеживаем процесс VNC (PID: $PID)..."
            tail --pid="$PID" -f /dev/null 2>/dev/null || {
                # Если tail не поддерживает --pid, используем цикл
                while ps -p "$PID" > /dev/null 2>&1; do
                    sleep 1
                done
                log "Процесс VNC завершен, выходим"
                exit 1
            }
            exit 0
        fi
    fi
    sleep 1
done

log "ПРЕДУПРЕЖДЕНИЕ: Не удалось найти процесс X сервера после 15 попыток"
log "Проверяем доступные команды VNC..."
which vncserver Xtigervnc Xvnc x11vnc 2>&1 | head -10 >&2 || true

log "Продолжаем работу в фоновом режиме для отладки..."
# fallback: sleep (prevent immediate exit, но логируем ошибку)
  sleep infinity
