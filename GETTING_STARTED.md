# Начало работы с Linux Training Simulator

Полное руководство по установке, настройке и использованию тренажёра. Проект работает на любой Debian-based системе (Debian, Ubuntu, Astra Linux, Linux Mint и др.).

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Установка на Astra Linux Special Edition](#установка-на-astra-linux-special-edition)
3. [Создание образов](#создание-образов)
4. [Тестирование миссий](#тестирование-миссий)
5. [Решение проблем](#решение-проблем)
6. [Быстрая справка](#быстрая-справка)

---

## Быстрый старт

### Автоматическая установка (Debian/Ubuntu/Astra Linux)

```bash
cd AstraDiplom
chmod +x scripts/quickstart.sh
./scripts/quickstart.sh
```

Скрипт автоматически:
- Определит ваш дистрибутив
- Установит все зависимости (Podman/Docker, Node.js, Python)
- Установит зависимости проекта
- Предложит создать образы контейнеров
- Создаст скрипт запуска

**Примечание**: При первом запуске вам нужно будет зарегистрироваться в системе.

### Ручная установка

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

## Установка на Astra Linux Special Edition

### Быстрый старт на Astra Linux

Самый простой способ - использовать скрипт быстрого старта:

```bash
cd AstraDiplom
chmod +x scripts/quickstart-astra.sh
./scripts/quickstart-astra.sh
```

Скрипт автоматически:
1. ✅ Установит все необходимые пакеты (Python, Node.js, Podman)
2. ✅ Настроит виртуальное окружение для backend
3. ✅ Установит зависимости frontend
4. ✅ Создаст скрипт запуска `start-trainer.sh`
5. ✅ Создаст ярлык на рабочем столе
6. ✅ Опционально создаст образ Astra Linux

### Установка Podman на Astra Linux

**Вариант 1: Использование Podman напрямую**

```bash
# Установка Podman
sudo apt install podman

# Настройка rootless режима
podman system migrate
```

**Вариант 2: Использование Docker с rootless-helper-astra**

```bash
# Установка rootless-helper-astra
sudo apt install rootless-helper-astra

# Включение пользовательских служб Docker для rootless режима
sudo systemctl start rootless-docker@<имя_пользователя>@<метка_безопасности>
sudo systemctl enable rootless-docker@<имя_пользователя>@<метка_безопасности>
```

### Особенности Astra Linux

**CD-ROM репозитории**: Astra Linux может быть настроена на использование CD-ROM как источника пакетов. Скрипт `quickstart-astra.sh` автоматически отключает CD-ROM репозитории.

**Проверка уязвимостей**: Astra Linux имеет встроенную проверку уязвимостей в пакетах. Скрипт `create-astra-image.sh` автоматически отключает проверку уязвимостей в chroot-окружении.

**Hardened ядро**: В hardened ядре отключены некоторые функции, необходимые для rootless контейнеров. Если вы используете hardened ядро, используйте привилегированный режим Podman.

**МКЦ (Мандатное управление доступом)**: При работе с МКЦ могут потребоваться дополнительные настройки меток безопасности. Обычно для тренажёра это не требуется, так как контейнеры изолированы.

---

## Создание образов

### Базовый образ (CLI-миссии)

```bash
cd scripts
./create-astra-image.sh
```

### Образ с VNC (GUI-миссии)

```bash
cd scripts
./create-astra-image.sh --vnc
```

**Подробнее**: [docs/PODMAN_GUIDE.md](docs/PODMAN_GUIDE.md) и [docs/VNC_GUIDE.md](docs/VNC_GUIDE.md)

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


# Получение VNC URL
curl http://localhost:8000/api/v1/sandbox/copy_file/vnc

# Проверка миссии
curl -X POST http://localhost:8000/api/v1/grader/check \
  -H "Content-Type: application/json" \
  -d '{"mission_id": "copy_file"}'
```

---

## Решение проблем

Подробное руководство по решению проблем: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

**Частые проблемы:**
- Образ не виден после создания → Используйте `./fix-podman-images.sh` или пересоздайте без sudo
- VNC не запускается → Проверьте логи: `podman logs <container_name>`
- Ошибки при сборке → Убедитесь, что файлы в `images/` существуют

---

## Быстрая справка

### Порты

| Порт | Сервис | Назначение |
|------|--------|------------|
| 3000 | Frontend | React приложение |
| 8000 | Backend | FastAPI сервер |
| 5900 | TigerVNC | VNC протокол |
| 6080 | noVNC | WebSocket (браузер) |

### Учетные данные VNC

- Пользователь: `astrauser` (или `sandboxuser` в зависимости от образа)
- Пароль: `astra123` (или `sandbox123`)

---

## Дополнительная документация

- **Podman и образы**: [docs/PODMAN_GUIDE.md](docs/PODMAN_GUIDE.md)
- **VNC**: [docs/VNC_GUIDE.md](docs/VNC_GUIDE.md)
- **Windows и WSL**: [docs/WINDOWS_DEVELOPMENT.md](docs/WINDOWS_DEVELOPMENT.md)
- **Решение проблем**: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Архитектура**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Создание миссий**: [docs/MISSIONS.md](docs/MISSIONS.md)
- **Скрипты**: [scripts/README.md](scripts/README.md)

---


