# Интеграция VNC в Astra Linux Training Simulator

## Обзор

Система использует TigerVNC и noVNC для предоставления доступа к графическому интерфейсу Astra Linux через веб-браузер. Это позволяет пользователям выполнять GUI-миссии (уровень A) без необходимости установки дополнительного ПО.

## Архитектура

```
┌─────────────┐      HTTP      ┌──────────────┐     WebSocket    ┌─────────────┐
│   Browser   │ ◄──────────────► │    noVNC     │ ◄───────────────► │ websockify  │
│  (Frontend) │                 │  (HTML5 VNC) │                  │   (proxy)   │
└─────────────┘                 └──────────────┘                  └─────────────┘
                                                                          │
                                                                          │ VNC
                                                                          ▼
                                                                   ┌─────────────┐
                                                                   │  TigerVNC   │
                                                                   │   Server    │
                                                                   └─────────────┘
                                                                          │
                                                                          ▼
                                                                   ┌─────────────┐
                                                                   │    XFCE     │
                                                                   │  Desktop    │
                                                                   └─────────────┘
```

## Компоненты

### 1. TigerVNC Server

**Назначение**: VNC сервер для Astra Linux, обеспечивает доступ к графическому рабочему столу.

**Особенности**:
- Официально поддерживается в Astra Linux
- Работает в режиме scraping (захват существующей сессии X11)
- Автоматический запуск без запроса разрешения

**Конфигурация**:
```bash
# Пароль VNC
vncpasswd -f > ~/.vnc/passwd

# Запуск без запроса разрешения
x0tigervncserver --localhost=0 --SecurityTypes=None
```

### 2. noVNC

**Назначение**: HTML5 VNC клиент, работает в браузере без плагинов.

**Особенности**:
- Полностью на JavaScript
- Поддержка WebSocket
- Поддержка буфера обмена
- Масштабирование и полноэкранный режим

**Установка**:
```bash
git clone https://github.com/novnc/noVNC.git /opt/noVNC
```

### 3. websockify

**Назначение**: Прокси между WebSocket (noVNC) и TCP (VNC).

**Установка**:
```bash
pip3 install websockify
```

**Запуск**:
```bash
/opt/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6080
```

### 4. XFCE Desktop

**Назначение**: Легковесное графическое окружение для Astra Linux.

**Преимущества**:
- Низкое потребление ресурсов
- Быстрый запуск
- Хорошая совместимость с VNC

## Сборка образа

### Автоматическая сборка

```bash
cd scripts
./build-astra-vnc-image.sh
```

Скрипт создаст образ `localhost/astra-linux:vnc` с предустановленными:
- TigerVNC Server
- noVNC
- websockify
- XFCE Desktop
- Supervisor (для автозапуска)

### Ручная сборка

```bash
podman build \
    -t localhost/astra-linux:vnc \
    -f images/Dockerfile.astra-vnc \
    .
```

## Использование

### Запуск контейнера с VNC

```bash
podman run -d \
    --name astra-vnc \
    -p 5900:5900 \
    -p 6080:6080 \
    localhost/astra-linux:vnc
```

**Порты**:
- `5900` - TigerVNC (для VNC клиентов)
- `6080` - noVNC (для браузера)

### Подключение

**Через браузер** (рекомендуется):
```
http://localhost:6080/vnc.html
```

**Через VNC клиент**:
```bash
vncviewer localhost:5900
```

**Учетные данные**:
- Пользователь: `astrauser`
- Пароль VNC: `astra123`

## API

### Создание песочницы с VNC

```http
POST /api/v1/sandbox/create
Content-Type: application/json

{
  "mission_id": "change_wallpaper",
  "level": "A",
  "image": "localhost/astra-linux:vnc",
  "use_vnc": true
}
```

**Ответ**:
```json
{
  "mission_id": "change_wallpaper",
  "container_name": "astra-trainer-change_wallpaper-20241211120000",
  "container_id": "abc123...",
  "status": "running",
  "vnc_port": 5900,
  "novnc_port": 6080,
  "vnc_url": "http://localhost:6080/vnc.html"
}
```

### Получение информации о VNC

```http
GET /api/v1/sandbox/{mission_id}/vnc
```

**Ответ**:
```json
{
  "mission_id": "change_wallpaper",
  "vnc_port": 5900,
  "novnc_port": 6080,
  "vnc_url": "http://localhost:6080/vnc.html",
  "ready": true
}
```

## Frontend интеграция

### Компонент SandboxViewer

Компонент автоматически определяет наличие VNC и отображает iframe с noVNC:

```jsx
<SandboxViewer missionId="change_wallpaper" level="A" />
```

**Функции**:
- Автоматическое подключение к noVNC
- Проверка готовности VNC сервера
- Индикатор состояния подключения
- Кнопка открытия в новом окне
- Поддержка полноэкранного режима

## Конфигурация

### Backend (config.py)

```python
# VNC/noVNC настройки
VNC_PORT_START: int = 5900
NOVNC_PORT_START: int = 6080
VNC_PASSWORD: str = "astra123"
VNC_RESOLUTION: str = "1280x720"
```

### Переменные окружения контейнера

```bash
DISPLAY=:0                    # X11 дисплей
VNC_PORT=5900                 # Порт VNC сервера
NOVNC_PORT=6080               # Порт noVNC
VNC_RESOLUTION=1280x720       # Разрешение экрана
VNC_DEPTH=24                  # Глубина цвета
```

## Автозапуск VNC

### Supervisor конфигурация

Файл `/etc/supervisor/conf.d/supervisord.conf`:

```ini
[program:vnc]
command=/usr/local/bin/start-vnc.sh
autostart=true
autorestart=true
priority=10

[program:dbus]
command=/usr/bin/dbus-daemon --system --nofork
autostart=true
autorestart=true
priority=5
```

### Скрипт запуска

Файл `/usr/local/bin/start-vnc.sh`:
- Очистка старых lock-файлов
- Запуск VNC сервера от пользователя `astrauser`
- Запуск noVNC/websockify
- Проверка готовности сервисов

## Решение проблем

### VNC сервер не запускается

**Проблема**: Контейнер запускается, но VNC недоступен.

**Решение**:
```bash
# Проверить логи контейнера
podman logs <container_name>

# Проверить процессы внутри
podman exec <container_name> ps aux | grep vnc

# Проверить порты
podman exec <container_name> netstat -tuln | grep -E "5900|6080"
```

### noVNC не подключается

**Проблема**: Браузер показывает ошибку подключения.

**Причины**:
1. VNC сервер еще не запустился (подождите 10-30 секунд)
2. Порты не проброшены
3. Firewall блокирует подключение

**Решение**:
```bash
# Проверить проброс портов
podman port <container_name>

# Проверить доступность noVNC
curl http://localhost:6080/

# Проверить websockify
podman exec <container_name> ps aux | grep websockify
```

### Черный экран в noVNC

**Проблема**: noVNC подключается, но показывает черный экран.

**Причины**:
1. XFCE не запустился
2. Проблемы с X11

**Решение**:
```bash
# Проверить XFCE процессы
podman exec <container_name> ps aux | grep xfce

# Проверить X11
podman exec <container_name> echo $DISPLAY
podman exec <container_name> xdpyinfo

# Перезапустить контейнер
podman restart <container_name>
```

### Низкая производительность

**Проблема**: VNC работает медленно, лагает.

**Решение**:
1. Уменьшить разрешение:
   ```bash
   VNC_RESOLUTION=1024x768
   ```

2. Уменьшить глубину цвета:
   ```bash
   VNC_DEPTH=16
   ```

3. Увеличить ресурсы контейнера:
   ```bash
   --memory 4G --cpus 4
   ```

## Безопасность

### Аутентификация

По умолчанию используется простой пароль VNC. Для продакшена:

1. **Генерировать случайный пароль** для каждой сессии
2. **Использовать TLS** для noVNC
3. **Ограничить время жизни** сессии

### Изоляция

- Контейнеры работают в rootless режиме
- VNC доступен только на localhost (требуется проброс портов)
- Каждая миссия в отдельном контейнере

### Рекомендации

1. Не используйте один пароль для всех пользователей
2. Настройте автоматическое завершение неактивных сессий
3. Логируйте все подключения
4. Используйте HTTPS для frontend

## Производительность

### Оптимизация

1. **Кэширование образов**: Используйте один базовый образ для всех миссий
2. **Предзапуск контейнеров**: Создавайте pool готовых контейнеров
3. **Ограничение ресурсов**: Устанавливайте лимиты CPU/RAM
4. **Очистка**: Автоматически удаляйте старые контейнеры

### Метрики

Рекомендуемые ресурсы на контейнер:
- **CPU**: 2 ядра
- **RAM**: 2 GB
- **Disk**: 1 GB

## Дополнительные возможности

### Запись сессии

Для записи действий пользователя:

```bash
# Установить vncrec
apt install vncrec

# Записать сессию
vncrec -record session.vnc localhost:5900
```

### Совместное использование

Для подключения нескольких пользователей к одной сессии:

```bash
# Запустить VNC с опцией AlwaysShared
vncserver -AlwaysShared
```

### Буфер обмена

noVNC поддерживает синхронизацию буфера обмена между браузером и VNC сессией через специальную панель.

## Ссылки

- [TigerVNC Documentation](https://tigervnc.org/)
- [noVNC GitHub](https://github.com/novnc/noVNC)
- [Astra Linux VNC Guide](https://wiki.astralinux.ru/)
- [XFCE Documentation](https://docs.xfce.org/)

