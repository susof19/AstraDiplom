# Начало работы с Astra Linux Training Simulator

Полное руководство по установке, настройке и использованию тренажёра.

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Создание образов](#создание-образов)
3. [Тестирование миссий](#тестирование-миссий)
4. [Решение проблем](#решение-проблем)
5. [Быстрая справка](#быстрая-справка)

---

## Быстрый старт

### Для Astra Linux (автоматическая установка)

```bash
cd AstraDiplom
chmod +x scripts/quickstart-astra.sh
./scripts/quickstart-astra.sh
```

Скрипт автоматически:
- Установит все зависимости (Podman, Node.js, Python)
- Установит зависимости проекта
- Предложит создать образы
- Создаст ярлык на рабочем столе

### Для других систем (ручная установка)

**1. Установите зависимости**:
```bash
# Podman
sudo apt install podman

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# Python 3.10+
sudo apt install python3 python3-venv python3-pip
```

**2. Установите зависимости проекта**:
```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend/web
npm install
```

**3. Создайте образы**:
```bash
cd scripts

# Проверка готовности
./check-setup.sh

# Базовый образ (CLI-миссии)
./create-astra-image.sh

# Образ с VNC (GUI-миссии)
./create-astra-image.sh --vnc
```

**4. Запустите приложение**:
```bash
# Backend (терминал 1)
cd backend
source venv/bin/activate
python run.py

# Frontend (терминал 2)
cd frontend/web
npm start
```

**5. Откройте в браузере**: http://localhost:3000

---

## Создание образов

### Проверка готовности

Перед созданием образов проверьте систему:

```bash
cd scripts
./check-setup.sh
```

Скрипт проверит:
- ✅ Установку Podman
- ✅ Наличие необходимых файлов
- ✅ Доступность реестра Astra Linux
- ✅ Существующие образы

### Создание базового образа

Для CLI-миссий (уровни B, C):

```bash
cd scripts
./create-astra-image.sh
```

Создаёт образ: `localhost/astra-linux:se`

### Создание образа с VNC

Для GUI-миссий (уровень A):

```bash
cd scripts
./create-astra-image.sh --vnc
```

**⚠️ Важно**: Базовый образ Astra Linux из реестра не содержит GUI пакетов (XFCE, TigerVNC).

**Варианты**:

1. **Упрощённая версия** (демонстрация)
   - Без реального VNC
   - Только для ознакомления со структурой

2. **Debian 12 как база** (рекомендуется для тестирования)
   - Полная поддержка VNC
   - XFCE Desktop
   - noVNC через браузер
   
3. **Полный образ Astra Linux** (если доступен)
   - Требует доступ к полному образу с GUI пакетами

**Для разработки рекомендуется**: Использовать Debian 12 или mock-режим на Windows

### Параметры скрипта

```bash
./create-astra-image.sh [OPTIONS]

Опции:
  --vnc              Создать образ с VNC
  --no-vnc           Создать базовый образ (по умолчанию)
  --rootless         Rootless режим (по умолчанию)
  --with-sudo        Использовать sudo
  --help             Показать справку
```

### Проверка образов

```bash
# Список образов
podman images

# Тестовый запуск базового
podman run --rm -it localhost/astra-linux:se /bin/bash

# Тестовый запуск VNC
podman run -d -p 5900:5900 -p 6080:6080 localhost/astra-linux:vnc
# Откройте: http://localhost:6080/vnc.html
```

---

## Тестирование миссий

### Доступные миссии

#### Уровень A (GUI) - требует VNC образ

**1. Копирование файла** (`copy_file`)
- Скопировать photo.jpg из Загрузки в Документы
- Использует файловый менеджер Thunar

**2. Изменение фона** (`change_wallpaper`)
- Изменить фон рабочего стола XFCE
- Выбрать изображение из папки Изображения

#### Уровень B (CLI) - базовый образ

**3. Создание архива** (`create_archive`)
- Создать backup.tar.gz из папки documents
- Команда: `tar -czf backup.tar.gz documents/`

**4. Поиск процессов** (`find_process`)
- Найти процесс test-daemon
- Сохранить PID в файл
- Команда: `pgrep test-daemon > daemon.pid`

#### Уровень C (Admin) - базовый образ

**5. Systemd сервис** (`systemd_service`)
- Создать unit-файл для сервиса
- Включить и запустить сервис

### Запуск тестирования

**1. Запустите приложение**:
```bash
# Backend
cd backend && source venv/bin/activate && python run.py

# Frontend (в другом терминале)
cd frontend/web && npm start
```

**2. Откройте**: http://localhost:3000

**3. Выберите миссию** и начните тестирование

### API для тестирования

```bash
# Создание песочницы (GUI)
curl -X POST http://localhost:8000/api/v1/sandbox/create \
  -H "Content-Type: application/json" \
  -d '{"mission_id": "copy_file", "level": "A", "use_vnc": true}'

# Создание песочницы (CLI)
curl -X POST http://localhost:8000/api/v1/sandbox/create \
  -H "Content-Type: application/json" \
  -d '{"mission_id": "create_archive", "level": "B", "use_vnc": false}'

# Получение VNC URL
curl http://localhost:8000/api/v1/sandbox/copy_file/vnc

# Проверка миссии
curl -X POST http://localhost:8000/api/v1/grader/check \
  -H "Content-Type: application/json" \
  -d '{"mission_id": "copy_file"}'
```

---

## Решение проблем

### Образ не виден после создания

**Проблема**: `podman images` показывает пустой список

**Причина**: Образ создан в root-контексте, проверяется в rootless

**Решение**:
```bash
# Пересоздать без sudo (рекомендуется)
cd scripts
./create-astra-image.sh --vnc

# Или перенести существующий
./fix-podman-images.sh
```

### Ошибка "Файл Dockerfile не найден"

**Решение**: Скрипт автоматически переходит в корень проекта. Если проблема сохраняется:

```bash
# Проверьте структуру
cd /путь/к/AstraDiplom
ls -la images/

# Запустите проверку
cd scripts
./check-setup.sh

# Запустите из корня
cd /путь/к/AstraDiplom
bash scripts/create-astra-image.sh --vnc
```

### Ошибка при сборке VNC образа: "no such file or directory"

**Проблема**: При сборке образа появляется ошибка `COPY start-vnc-simple.sh /usr/local/bin/start-vnc.sh: no such file or directory`

**Причина**: Dockerfile использует относительные пути, которые должны быть указаны относительно контекста сборки (корня проекта).

**Решение**: Все Dockerfile уже исправлены и используют правильные пути `images/start-vnc.sh` и `images/supervisord.conf`. Если ошибка повторяется:

```bash
# Убедитесь, что файлы существуют
ls -la images/start-vnc*.sh images/supervisord*.conf

# Пересоберите образ
cd scripts
sudo bash create-astra-image.sh --vnc

# Выберите вариант 1 (упрощенный) или 2 (Debian 12)
```

### Ошибка "Не удалось загрузить образ из реестра"

**Решение**:
```bash
# Проверьте доступность
curl -I https://registry.astralinux.ru/

# Используйте альтернативный образ
podman pull debian:12
podman tag debian:12 localhost/astra-linux:se

# Или другой digest
podman pull registry.astralinux.ru/library/astra/ubi18:1.8.1
```

### VNC не запускается

**Проблема**: Контейнер запущен, но VNC недоступен

**Решение**:
```bash
# Проверить логи
podman logs <container_name>

# Проверить процессы
podman exec <container_name> ps aux | grep vnc

# Подождать 30-60 секунд (первый запуск)

# Перезапустить
podman restart <container_name>
```

### Черный экран в noVNC

**Причины**: VNC сервер еще запускается или XFCE не запустился

**Решение**:
```bash
# Проверить XFCE
podman exec <container_name> ps aux | grep xfce

# Проверить X11
podman exec <container_name> echo $DISPLAY

# Перезапустить контейнер
podman restart <container_name>
```

---

## Быстрая справка

### Команды создания образов

```bash
cd scripts

# Проверка
./check-setup.sh

# Базовый образ
./create-astra-image.sh

# Образ с VNC
./create-astra-image.sh --vnc

# Справка
./create-astra-image.sh --help
```

### Проверка образов

```bash
# Список
podman images

# Тест базового
podman run --rm -it localhost/astra-linux:se /bin/bash

# Тест VNC
podman run -d -p 5900:5900 -p 6080:6080 localhost/astra-linux:vnc
```

### Запуск приложения

```bash
# Backend
cd backend
source venv/bin/activate
python run.py

# Frontend (другой терминал)
cd frontend/web
npm start
```

### Учетные данные

**VNC**:
- Пользователь: `astrauser`
- Пароль: `astra123`

### Структура образов

- `localhost/astra-linux:se` - базовый (CLI)
- `localhost/astra-linux:vnc` - с VNC (GUI)

### Порты

| Порт | Сервис | Назначение |
|------|--------|------------|
| 3000 | Frontend | React приложение |
| 8000 | Backend | FastAPI сервер |
| 5900 | TigerVNC | VNC протокол |
| 6080 | noVNC | WebSocket (браузер) |

---

## Дополнительная документация

### Подробные руководства

- **Podman**: [docs/PODMAN_GUIDE.md](docs/PODMAN_GUIDE.md)
- **VNC**: [docs/VNC_GUIDE.md](docs/VNC_GUIDE.md)
- **Архитектура**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Создание миссий**: [docs/MISSIONS.md](docs/MISSIONS.md)

### Установка

- **Astra Linux**: [docs/ASTRA_LINUX.md](docs/ASTRA_LINUX.md)
- **Windows**: [docs/WINDOWS_DEVELOPMENT.md](docs/WINDOWS_DEVELOPMENT.md)
- **Детальная настройка**: [docs/SETUP.md](docs/SETUP.md)

### Решение проблем

- **Общие проблемы**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

### Разработка

- **Вклад в проект**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Скрипты**: [scripts/README.md](scripts/README.md)

---

## Контрольный список

### Перед началом работы

- [ ] Podman установлен
- [ ] Node.js 18+ установлен
- [ ] Python 3.10+ установлен
- [ ] Зависимости проекта установлены
- [ ] Образы созданы
- [ ] Backend запущен
- [ ] Frontend запущен

### Проверка работоспособности

- [ ] `podman images` показывает образы astra-linux
- [ ] Backend доступен на http://localhost:8000
- [ ] Frontend доступен на http://localhost:3000
- [ ] VNC работает (для GUI-миссий)

---

## Полезные команды

```bash
# Информация о Podman
podman info

# Список контейнеров
podman ps -a

# Логи контейнера
podman logs <container_name>

# Остановить контейнер
podman stop <container_name>

# Удалить контейнер
podman rm <container_name>

# Очистить неиспользуемые образы
podman image prune -a

# Проверка миссий
find missions -name "mission.yaml" | wc -l
```

---

## Поддержка

Если возникли проблемы:

1. Запустите `./scripts/check-setup.sh`
2. Проверьте документацию в `docs/`
3. Посмотрите логи: `podman logs <container>`
4. Создайте issue с описанием проблемы

