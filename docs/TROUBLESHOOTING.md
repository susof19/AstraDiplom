# Устранение неполадок

Этот документ содержит решения наиболее распространённых проблем при работе с Linux Training Simulator.

## Содержание

1. [Проблемы с Backend и API](#проблемы-с-backend-и-api)
2. [Проблемы с базой данных](#проблемы-с-базой-данных)
3. [Проблемы с видимостью образов Podman](#проблемы-с-видимостью-образов-podman)
4. [Проблемы с созданием образа](#проблемы-с-созданием-образа)
5. [Проблемы с VNC образами](#проблемы-с-vnc-образами)
6. [Проблемы с запуском контейнеров](#проблемы-с-запуском-контейнеров)
7. [Проблемы с портами и сетью](#проблемы-с-портами-и-сетью)

---

## Проблемы с Backend и API

### Проблема: 404 ошибка при регистрации/входе

#### Шаг 1: Проверьте, что backend запущен

```bash
# Проверьте, что backend отвечает
curl http://localhost:8000/health

# Должен вернуть: {"status":"healthy"}
```

#### Шаг 2: Проверьте доступные роуты

```bash
# Проверьте список всех роутов
curl http://localhost:8000/api/v1/routes

# Должен показать список всех доступных роутов, включая /api/v1/auth/register
```

#### Шаг 3: Проверьте логи backend

```bash
# Если используете start-demo.sh
tail -f backend.log

# Или если запускаете вручную, смотрите вывод в терминале
```

В логах должны быть:
- `✅ Все роуты зарегистрированы`
- `✅ Соединение с базой данных установлено`
- `✅ Таблицы базы данных готовы`

#### Шаг 4: Проверьте, что backend слушает на правильном адресе

Backend по умолчанию слушает на `0.0.0.0:8000`, что означает "все интерфейсы". Это правильно и должно работать с `localhost:8000`.

Если проблема сохраняется, проверьте:

```bash
# Проверьте, что порт 8000 слушается
netstat -tuln | grep 8000
# или
ss -tuln | grep 8000

# Должно показать что-то вроде:
# 0.0.0.0:8000 или :::8000
```

#### Шаг 5: Проверьте proxy frontend

Frontend использует proxy для подключения к backend. Убедитесь, что файл `frontend/web/src/setupProxy.js` существует и настроен правильно:

```javascript
target: 'http://localhost:8000',
```

#### Шаг 6: Проверьте CORS

Если видите ошибки CORS в консоли браузера, убедитесь, что в `backend/config.py` правильно настроены `ALLOWED_ORIGINS`:

```python
ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
```

### Backend не запускается

**Причина**: Ошибка подключения к БД или отсутствие зависимостей

**Решение**:
1. Проверьте, что PostgreSQL запущен: `sudo systemctl status postgresql`
2. Инициализируйте БД: `cd backend && source venv/bin/activate && python init_db.py`
3. Проверьте `DATABASE_URL` в `backend/config.py`

### Роуты возвращают 404

**Причина**: Роуты не зарегистрированы или неправильный URL

**Решение**:
1. Проверьте логи backend - должны быть сообщения о регистрации роутов
2. Проверьте доступные роуты: `curl http://localhost:8000/api/v1/routes`
3. Убедитесь, что frontend использует правильный URL (через proxy)

---

## Проблемы с базой данных

### Ошибка подключения к БД

**Причина**: PostgreSQL не запущен или неправильные учетные данные

**Решение**:
1. Запустите PostgreSQL:
   ```bash
   # Linux
   sudo systemctl start postgresql
   
   # WSL
   sudo service postgresql start
   ```

2. Проверьте учетные данные в `backend/config.py`:
   ```python
   DATABASE_URL: str = "postgresql://trainer_user:trainer_password@localhost:5432/trainer_db"
   ```

3. Выполните проверку БД:
   ```bash
   ./scripts/setup-database.sh
   ```

4. Или инициализируйте БД вручную:
   ```bash
   cd backend
   source venv/bin/activate
   python init_db.py
   ```

---

## Проблемы с видимостью образов Podman

### Образ создан, но `podman images` показывает пустой список

**Решение**:
```bash
# Вариант 1: Пересоздать без sudo
cd scripts
./create-astra-image.sh --vnc

# Вариант 2: Перенести существующий
./fix-podman-images.sh
```

**Подробнее**: [PODMAN_GUIDE.md](PODMAN_GUIDE.md)

### Ошибка "short-name did not resolve"

**Решение**: Используйте `localhost/` префикс:
```bash
podman run --rm -it localhost/astra-linux:se /bin/bash
```

---

## Проблемы с созданием образа

### Ошибка "Couldn't find these debs: perl-modules-5.28"

**Решение**: Используйте обновлённый скрипт, который автоматически определяет версию:
```bash
cd scripts
./create-astra-image.sh --vnc
```

### Ошибка "Репозиторий не содержит файла Release"

**Решение**: Проверьте доступность репозитория:
```bash
curl -I http://dl.astralinux.ru/astra/stable/1.8_x86-64/repository-main/
```

**Подробнее**: [PODMAN_GUIDE.md](PODMAN_GUIDE.md)

---

## Проблемы с VNC

### XFCE пакеты недоступны в образе Astra Linux

**Ошибка**:
```
E: Package 'xfce4' has no installation candidate
E: Unable to locate package xfce4-terminal
E: Unable to locate package xfce4-goodies
```

**Причина**: Базовый образ Astra Linux из реестра (`registry.astralinux.ru/library/astra/ubi18`) является **минимальным** и не содержит:
- GUI пакетов (XFCE, GNOME, KDE)
- TigerVNC Server
- X11 компонентов

Это нормально для серверного образа, но не подходит для GUI-миссий.

**Решения**:

#### Решение 1: Использовать Debian 12 (рекомендуется для разработки)

```bash
cd scripts
./create-astra-image.sh --vnc
# Выберите вариант 2: Debian 12
```

**Преимущества**:
- ✅ Все пакеты доступны
- ✅ Полная поддержка VNC
- ✅ XFCE Desktop работает
- ✅ Подходит для тестирования

**Недостатки**:
- ⚠️ Это не настоящий Astra Linux
- ⚠️ Некоторые специфичные для Astra функции могут отсутствовать

#### Решение 2: Использовать готовый образ из репозитория shinbatsu/astra-ui-vnc-container

```bash
./scripts/setup-astra-vnc-image.sh
```

**Примечание**: Этот образ может требовать приватный базовый образ. Если сборка не удалась, используйте Решение 1 или 3.

#### Решение 3: Использовать Mock-режим (для Windows)

```bash
# В backend/.env или config.py
MOCK_SANDBOX=true
```

**Преимущества**:
- ✅ Не требует Docker/Podman
- ✅ Быстрая разработка
- ✅ Тестирование логики без контейнеров

**Недостатки**:
- ⚠️ Нет реальной песочницы
- ⚠️ Только для разработки UI

#### Решение 4: Использовать только CLI-миссии

Базовый образ отлично подходит для CLI-миссий (уровни B и C):

```bash
cd scripts
./create-astra-image.sh  # Без --vnc
```

Миссии уровня B и C не требуют GUI и будут работать отлично.

### Проблема: Ошибки dbus в логах

**Ошибка**: `dbus exited (exit status 1)` в логах supervisor

**Причина**: Это нормально. dbus запускается через `dbus-launch` внутри VNC-сессии, отдельный системный dbus не требуется.

**Решение**: Игнорировать эти ошибки - они не критичны, VNC работает корректно.

### Проблема: Темное окно с только noVNC UI

**Причина**: XFCE Desktop Environment не запускается корректно.

**Решение**:
1. Убедитесь, что используется актуальный Dockerfile с полным набором XFCE пакетов
2. Проверьте логи контейнера: `docker logs <container_id>` или `podman logs <container_id>`
3. Пересоберите образ с обновленным Dockerfile

---

## Проблемы с запуском контейнеров

### Проблема: Образ создаётся, но контейнер не запускается

**Решение**:

1. **Проверьте образ:**
   ```bash
   podman images | grep astra-linux
   # или
   docker images | grep astra-linux
   ```

2. **Проверьте запуск:**
   ```bash
   podman run --rm -it localhost/astra-linux:se /bin/bash
   # или
   docker run --rm -it localhost/astra-linux:se /bin/bash
   ```

3. **Если ошибка с правами (rootless режим):**
   ```bash
   podman run --rm -it --userns=keep-id localhost/astra-linux:se /bin/bash
   ```

4. **Проверьте версию образа:**
   ```bash
   podman run --rm localhost/astra-linux:se cat /etc/os-release
   ```

### Проблема: Ошибка с user_namespaces

**Причина**: В hardened ядре Astra Linux отключены user_namespaces (CONFIG_USER_NS), необходимые для rootless контейнеров.

**Решение**: Используйте привилегированный режим Podman или используйте обычное (не hardened) ядро.

---

## Проблемы с портами и сетью

### Порт занят

Если порт 3000 или 8000 занят:

```bash
# Проверьте, что использует порт
sudo lsof -i :8000
sudo lsof -i :3000
# или
sudo ss -tuln | grep -E ':(3000|8000)'

# Остановите процесс или измените порт в config.py
```

### VNC не доступен в WSL

**Решение**:
1. Убедитесь, что Docker Desktop запущен в Windows
2. Проверьте логи контейнера: `podman logs <container_name>`
3. Перезапустите WSL: `wsl --shutdown` (в PowerShell)

### Проблемы с сетью в WSL

**Решение**: Перезапустите WSL: `wsl --shutdown` (в PowerShell), затем откройте снова

**Подробнее**: [WINDOWS_DEVELOPMENT.md](WINDOWS_DEVELOPMENT.md)

---

## Дополнительная информация

- [PODMAN_GUIDE.md](PODMAN_GUIDE.md) - Работа с Podman и создание образов
- [VNC_GUIDE.md](VNC_GUIDE.md) - Решение проблем с VNC
- [WINDOWS_DEVELOPMENT.md](WINDOWS_DEVELOPMENT.md) - Разработка на Windows и WSL
