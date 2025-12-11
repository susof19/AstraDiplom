# Быстрый старт с VNC

## 🚀 Запуск за 3 шага

### Шаг 1: Сборка образа с VNC

```bash
cd scripts
./build-astra-vnc-image.sh
```

Это создаст образ `localhost/astra-linux:vnc` с предустановленными:
- ✅ TigerVNC Server
- ✅ noVNC (HTML5 VNC клиент)
- ✅ XFCE Desktop
- ✅ Автозапуск VNC

### Шаг 2: Тестовый запуск

```bash
podman run -d \
    --name astra-vnc-test \
    -p 5900:5900 \
    -p 6080:6080 \
    localhost/astra-linux:vnc
```

### Шаг 3: Подключение

Откройте в браузере:
```
http://localhost:6080/vnc.html
```

**Учетные данные**:
- Пользователь: `astrauser`
- Пароль: `astra123`

## 🎮 Использование в проекте

### Backend

Образ автоматически используется для миссий уровня A:

```python
# В backend/sandbox/container.py
sandbox = ContainerSandbox(
    mission_id="change_wallpaper",
    level="A",
    use_vnc=True  # По умолчанию включено
)
```

### Frontend

Компонент `SandboxViewer` автоматически отображает VNC:

```jsx
<SandboxViewer missionId="change_wallpaper" level="A" />
```

## 🔧 Проверка работы

### 1. Проверить запуск контейнера

```bash
podman ps
```

Должен показать контейнер с портами `5900` и `6080`.

### 2. Проверить VNC сервер

```bash
# Проверить порты
podman exec astra-vnc-test netstat -tuln | grep -E "5900|6080"

# Проверить процессы
podman exec astra-vnc-test ps aux | grep vnc
```

### 3. Проверить noVNC

```bash
curl http://localhost:6080/
```

Должен вернуть HTML страницу noVNC.

## 📋 Порты

| Порт | Сервис | Назначение |
|------|--------|------------|
| 5900 | TigerVNC | VNC протокол (для VNC клиентов) |
| 6080 | noVNC | WebSocket прокси (для браузера) |

## 🛠️ Решение проблем

### Проблема: Образ не собирается

**Решение**:
```bash
# Проверить доступность базового образа
podman pull registry.astralinux.ru/library/astra/ubi18@sha256:850a91072ae82fcd7c718e979d044bd8f4a218a1f7938c23d98d019e1b5e7bfa

# Или использовать альтернативный базовый образ
BASE_IMAGE=debian:12 ./build-astra-vnc-image.sh
```

### Проблема: VNC не запускается

**Решение**:
```bash
# Посмотреть логи
podman logs astra-vnc-test

# Проверить supervisor
podman exec astra-vnc-test supervisorctl status
```

### Проблема: Черный экран в браузере

**Причина**: VNC сервер еще запускается (обычно 10-30 секунд).

**Решение**: Подождите и обновите страницу.

### Проблема: Низкая производительность

**Решение**: Уменьшите разрешение экрана:

```bash
podman run -d \
    --name astra-vnc-test \
    -p 5900:5900 \
    -p 6080:6080 \
    -e VNC_RESOLUTION=1024x768 \
    localhost/astra-linux:vnc
```

## 🎯 Настройка

### Изменить разрешение экрана

```bash
-e VNC_RESOLUTION=1920x1080  # Full HD
-e VNC_RESOLUTION=1280x720   # HD (по умолчанию)
-e VNC_RESOLUTION=1024x768   # Низкое (быстрее)
```

### Изменить пароль VNC

Отредактируйте `images/Dockerfile.astra-vnc`:

```dockerfile
# Заменить
RUN echo "astra123" | vncpasswd -f > /home/astrauser/.vnc/passwd

# На
RUN echo "ваш_пароль" | vncpasswd -f > /home/astrauser/.vnc/passwd
```

Пересоберите образ.

### Увеличить ресурсы

```bash
podman run -d \
    --name astra-vnc-test \
    --memory 4G \
    --cpus 4 \
    -p 5900:5900 \
    -p 6080:6080 \
    localhost/astra-linux:vnc
```

## 📚 Дополнительная информация

- **Подробная документация**: [docs/VNC_INTEGRATION.md](docs/VNC_INTEGRATION.md)
- **Решение проблем**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Архитектура**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 💡 Советы

1. **Используйте полноэкранный режим** в noVNC для лучшего опыта
2. **Закрывайте неиспользуемые контейнеры** для экономии ресурсов
3. **Используйте один базовый образ** для всех миссий
4. **Настройте автоочистку** старых контейнеров

## 🔄 Остановка и очистка

```bash
# Остановить контейнер
podman stop astra-vnc-test

# Удалить контейнер (автоматически при --rm)
podman rm astra-vnc-test

# Удалить образ
podman rmi localhost/astra-linux:vnc
```

## ✅ Готово!

Теперь вы можете использовать VNC для GUI-миссий в Astra Linux Training Simulator!

Для интеграции в проект просто запустите backend и frontend - VNC будет работать автоматически для миссий уровня A.

