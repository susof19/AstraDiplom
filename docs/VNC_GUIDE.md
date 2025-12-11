# Руководство по VNC в Astra Linux Training Simulator

Полное руководство по использованию VNC для GUI-миссий через веб-браузер.

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Архитектура](#архитектура)
3. [Создание образа с VNC](#создание-образа-с-vnc)
4. [Использование](#использование)
5. [Решение проблем](#решение-проблем)
6. [Настройка](#настройка)

---

## Быстрый старт

### За 3 шага

**1. Создать образ с VNC**
```bash
cd scripts
./create-astra-image.sh --vnc
```

**2. Тестовый запуск**
```bash
podman run -d \
    --name astra-vnc-test \
    -p 5900:5900 \
    -p 6080:6080 \
    localhost/astra-linux:vnc
```

**3. Открыть в браузере**
```
http://localhost:6080/vnc.html
```

**Учетные данные**:
- Пользователь: `astrauser`
- Пароль: `astra123`

---

## Архитектура

### Компоненты

```
Browser → noVNC (HTML5) → websockify → TigerVNC → XFCE Desktop
```

**TigerVNC Server**:
- Официальный VNC для Astra Linux
- Автоматический запуск без запроса разрешения
- Порт: 5900

**noVNC**:
- HTML5 VNC клиент
- Работает в браузере без плагинов
- Порт: 6080

**websockify**:
- Прокси WebSocket ↔ TCP
- Связывает noVNC с TigerVNC

**XFCE Desktop**:
- Легковесное окружение
- Быстрый запуск
- Низкое потребление ресурсов

### Схема работы

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

---

## Создание образа с VNC

### Автоматическое создание

```bash
cd scripts
./create-astra-image.sh --vnc
```

Скрипт создаёт образ `localhost/astra-linux:vnc` с предустановленными:
- ✅ TigerVNC Server
- ✅ noVNC
- ✅ websockify
- ✅ XFCE Desktop
- ✅ Supervisor (автозапуск)

### Что включено

**Базовые пакеты**:
- `tigervnc-standalone-server` - VNC сервер
- `tigervnc-scraping-server` - захват сессии
- `xfce4` - графическое окружение
- `python3`, `git` - для noVNC

**Автозапуск**:
- Supervisor управляет процессами
- VNC запускается автоматически
- noVNC доступен сразу после старта

**Настройки по умолчанию**:
- Разрешение: 1280x720
- Глубина цвета: 24 бит
- Пользователь: astrauser
- Пароль VNC: astra123

---

## Использование

### В проекте

Backend автоматически использует VNC для миссий уровня A:

```python
# Создание песочницы с VNC
sandbox = await sandbox_manager.create_sandbox(
    mission_id="change_wallpaper",
    level="A",
    use_vnc=True  # По умолчанию включено
)

# Получение URL для подключения
vnc_url = await sandbox.get_vnc_url()
# Результат: "http://localhost:6080/vnc.html"
```

Frontend автоматически отображает VNC:

```jsx
<SandboxViewer missionId="change_wallpaper" level="A" />
```

### API

**Создание песочницы с VNC**:
```http
POST /api/v1/sandbox/create
Content-Type: application/json

{
  "mission_id": "change_wallpaper",
  "level": "A",
  "use_vnc": true
}
```

**Получение информации о VNC**:
```http
GET /api/v1/sandbox/{mission_id}/vnc
```

### Прямое использование

```bash
# Запуск контейнера
podman run -d \
    --name my-astra \
    -p 5900:5900 \
    -p 6080:6080 \
    localhost/astra-linux:vnc

# Подключение через браузер
http://localhost:6080/vnc.html

# Подключение через VNC клиент
vncviewer localhost:5900

# Остановка
podman stop my-astra
```

---

## Решение проблем

### VNC сервер не запускается

**Симптомы**: Контейнер запущен, но VNC недоступен.

**Диагностика**:
```bash
# Проверить логи
podman logs <container_name>

# Проверить процессы
podman exec <container_name> ps aux | grep vnc

# Проверить порты
podman exec <container_name> netstat -tuln | grep -E "5900|6080"
```

**Решение**: Обычно VNC запускается за 10-30 секунд. Подождите и проверьте снова.

### Черный экран в noVNC

**Причины**:
1. VNC сервер еще запускается
2. XFCE не запустился
3. Проблемы с X11

**Решение**:
```bash
# Проверить XFCE
podman exec <container_name> ps aux | grep xfce

# Проверить X11
podman exec <container_name> echo $DISPLAY
podman exec <container_name> xdpyinfo

# Перезапустить контейнер
podman restart <container_name>
```

### noVNC не подключается

**Причины**:
1. VNC сервер еще не готов
2. Порты не проброшены
3. Firewall блокирует

**Решение**:
```bash
# Проверить проброс портов
podman port <container_name>

# Проверить доступность noVNC
curl http://localhost:6080/

# Проверить websockify
podman exec <container_name> ps aux | grep websockify
```

### Низкая производительность

**Решение 1**: Уменьшить разрешение
```bash
podman run -d \
    -e VNC_RESOLUTION=1024x768 \
    -p 5900:5900 -p 6080:6080 \
    localhost/astra-linux:vnc
```

**Решение 2**: Уменьшить глубину цвета
```bash
podman run -d \
    -e VNC_DEPTH=16 \
    -p 5900:5900 -p 6080:6080 \
    localhost/astra-linux:vnc
```

**Решение 3**: Увеличить ресурсы
```bash
podman run -d \
    --memory 4G --cpus 4 \
    -p 5900:5900 -p 6080:6080 \
    localhost/astra-linux:vnc
```

---

## Настройка

### Переменные окружения

```bash
DISPLAY=:0                    # X11 дисплей
VNC_PORT=5900                 # Порт VNC сервера
NOVNC_PORT=6080               # Порт noVNC
VNC_RESOLUTION=1280x720       # Разрешение экрана
VNC_DEPTH=24                  # Глубина цвета (16/24/32)
```

### Backend настройки

Файл `backend/config.py`:

```python
# VNC/noVNC настройки
VNC_PORT_START: int = 5900        # Начальный порт для VNC
NOVNC_PORT_START: int = 6080      # Начальный порт для noVNC
VNC_PASSWORD: str = "astra123"    # Пароль VNC
VNC_RESOLUTION: str = "1280x720"  # Разрешение экрана
```

### Изменение пароля

Отредактируйте `images/Dockerfile.astra-vnc`:

```dockerfile
# Заменить
RUN echo "astra123" | vncpasswd -f > /home/astrauser/.vnc/passwd

# На
RUN echo "ваш_пароль" | vncpasswd -f > /home/astrauser/.vnc/passwd
```

Пересоберите образ:
```bash
./create-astra-image.sh --vnc
```

### Порты

| Порт | Сервис | Назначение |
|------|--------|------------|
| 5900 | TigerVNC | VNC протокол (для VNC клиентов) |
| 6080 | noVNC | WebSocket прокси (для браузера) |

---

## Дополнительные возможности

### Запись сессии

```bash
# Установить vncrec
apt install vncrec

# Записать сессию
vncrec -record session.vnc localhost:5900
```

### Совместное использование

Для подключения нескольких пользователей:

```bash
vncserver -AlwaysShared
```

### Буфер обмена

noVNC поддерживает синхронизацию буфера обмена через специальную панель (иконка в левом меню noVNC).

---

## Безопасность

### Рекомендации

1. **Генерируйте случайные пароли** для каждой сессии
2. **Используйте TLS** для noVNC в продакшене
3. **Ограничивайте время жизни** сессий
4. **Логируйте подключения**

### Изоляция

- Контейнеры работают в rootless режиме
- VNC доступен только на localhost
- Каждая миссия в отдельном контейнере

---

## Производительность

### Рекомендуемые ресурсы

На контейнер:
- **CPU**: 2 ядра
- **RAM**: 2 GB
- **Disk**: 1 GB

### Оптимизация

1. **Кэширование образов** - используйте один базовый образ
2. **Предзапуск** - создавайте pool готовых контейнеров
3. **Ограничение ресурсов** - устанавливайте лимиты
4. **Автоочистка** - удаляйте старые контейнеры

---

## Ссылки

- [TigerVNC Documentation](https://tigervnc.org/)
- [noVNC GitHub](https://github.com/novnc/noVNC)
- [Astra Linux VNC Guide](https://wiki.astralinux.ru/)
- [XFCE Documentation](https://docs.xfce.org/)

