#!/bin/bash
# Упрощённый скрипт запуска noVNC (без реального VNC)
# Для демонстрации и тестирования

set -e

echo "🚀 Запуск упрощённого VNC сервера..."
echo "⚠️  Внимание: Это упрощённая версия без реального VNC"
echo "   Для полной функциональности требуется установка TigerVNC"

NOVNC_PORT=${NOVNC_PORT:-6080}

# Запуск noVNC в режиме демонстрации
echo "🌐 Запуск noVNC на порту $NOVNC_PORT..."

cd /opt/noVNC

# Создаём простую HTML страницу с информацией
cat > /opt/noVNC/info.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Astra Linux VNC - Информация</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { color: #0066cc; }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }
        .info {
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 20px 0;
        }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Astra Linux Training Simulator - VNC</h1>
        
        <div class="warning">
            <strong>⚠️ Упрощённая версия</strong><br>
            Это упрощённая версия без полной поддержки VNC.<br>
            В базовом образе Astra Linux отсутствуют необходимые пакеты.
        </div>
        
        <div class="info">
            <strong>ℹ️ Что нужно для полной функциональности:</strong>
            <ul>
                <li>TigerVNC Server (tigervnc-standalone-server)</li>
                <li>XFCE Desktop Environment (xfce4)</li>
                <li>X11 Server (xorg)</li>
            </ul>
        </div>
        
        <h2>Решение</h2>
        <p>Используйте один из вариантов:</p>
        
        <h3>1. Использовать Debian образ (для тестирования)</h3>
        <code>podman pull debian:12</code><br>
        <code>podman tag debian:12 localhost/astra-linux:se</code><br>
        <code>./create-astra-image.sh --vnc</code>
        
        <h3>2. Использовать полный образ Astra Linux</h3>
        <p>Если у вас есть доступ к полному образу Astra Linux с GUI пакетами</p>
        
        <h3>3. Использовать CLI-миссии</h3>
        <p>Базовый образ подходит для CLI-миссий (уровни B и C)</p>
        <code>./create-astra-image.sh</code>
        
        <h2>Контейнер работает!</h2>
        <p>✅ Контейнер успешно запущен<br>
        ✅ noVNC доступен<br>
        ❌ VNC сервер не установлен (отсутствуют пакеты)</p>
        
        <p><a href="/">← Вернуться на главную</a></p>
    </div>
</body>
</html>
EOF

# Запускаем простой HTTP сервер на Python
python3 -m http.server $NOVNC_PORT 2>&1 | tee /tmp/novnc.log &

echo ""
echo "✅ Сервер запущен на порту $NOVNC_PORT"
echo "🌐 Откройте: http://localhost:$NOVNC_PORT/info.html"
echo ""

# Держим скрипт запущенным
wait

