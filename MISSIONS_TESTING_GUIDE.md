# Руководство по тестированию миссий

## Обновлённые миссии для тестирования

### Уровень A (GUI) - Требует VNC образ

#### 1. Копирование файла
**Файл**: `missions/level_a/copy_file/mission.yaml`

**Задача**: Скопировать файл photo.jpg из папки Загрузки в папку Документы

**Тестовые файлы**:
- `/home/astrauser/Загрузки/photo.jpg` (создаётся автоматически)

**Проверка**:
- Файл существует в `/home/astrauser/Документы/photo.jpg`

**Как тестировать**:
1. Запустить контейнер с VNC
2. Открыть файловый менеджер Thunar
3. Перейти в Загрузки
4. Скопировать photo.jpg (Ctrl+C)
5. Перейти в Документы
6. Вставить (Ctrl+V)

---

#### 2. Изменение фона рабочего стола
**Файл**: `missions/level_a/change_wallpaper/mission.yaml`

**Задача**: Изменить фон рабочего стола на изображение из папки Изображения

**Тестовые файлы**:
- `/home/astrauser/Изображения/astra-wallpaper-1.jpg`
- `/home/astrauser/Изображения/astra-wallpaper-2.jpg`

**Проверка**:
- Путь к фону содержит `/home/astrauser/Изображения`

**Как тестировать**:
1. Запустить контейнер с VNC
2. Щёлкнуть правой кнопкой на рабочем столе
3. Выбрать "Параметры рабочего стола"
4. Выбрать изображение из папки Изображения
5. Нажать "Закрыть"

---

### Уровень B (CLI) - Базовый образ

#### 3. Создание архива
**Файл**: `missions/level_b/create_archive/mission.yaml`

**Задача**: Создать архив backup.tar.gz из папки documents

**Тестовые файлы**:
- `/home/astrauser/documents/file1.txt`
- `/home/astrauser/documents/file2.txt`
- `/home/astrauser/documents/file3.txt`

**Проверка**:
- Архив существует: `/home/astrauser/backup.tar.gz`
- Архив содержит 3 файла

**Команда**:
```bash
tar -czf backup.tar.gz documents/
```

**Как тестировать**:
1. Запустить контейнер
2. Выполнить команду создания архива
3. Проверить: `tar -tzf backup.tar.gz`

---

#### 4. Поиск процессов
**Файл**: `missions/level_b/find_process/mission.yaml`

**Задача**: Найти процесс test-daemon и сохранить его PID

**Проверка**:
- Файл `/home/astrauser/daemon.pid` содержит число

**Команды**:
```bash
# Вариант 1
pgrep test-daemon > daemon.pid

# Вариант 2
ps aux | grep test-daemon | awk '{print $2}' | head -1 > daemon.pid
```

**Как тестировать**:
1. Запустить контейнер
2. Найти PID процесса
3. Сохранить в файл

---

### Уровень C (Admin) - Базовый образ

#### 5. Создание systemd сервиса
**Файл**: `missions/level_c/systemd_service/mission.yaml`

**Задача**: Создать systemd сервис test-service

**Тестовые файлы**:
- `/usr/local/bin/test-service.sh` (скрипт сервиса)

**Проверка**:
- Unit-файл создан: `/etc/systemd/system/test-service.service`
- Сервис включен: `systemctl is-enabled test-service`
- Сервис запущен: `systemctl is-active test-service`

**Пример unit-файла**:
```ini
[Unit]
Description=Test Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/test-service.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

**Команды**:
```bash
# Создать unit-файл
sudo nano /etc/systemd/system/test-service.service

# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable test-service

# Запустить сервис
sudo systemctl start test-service

# Проверить статус
sudo systemctl status test-service
```

---

## Запуск тестирования

### 1. Создать образы

```bash
cd scripts

# Базовый образ (для уровней B, C)
./create-astra-image.sh

# Образ с VNC (для уровня A)
./create-astra-image.sh --vnc
```

### 2. Запустить backend

```bash
cd backend
source venv/bin/activate
python run.py
```

### 3. Запустить frontend

```bash
cd frontend/web
npm start
```

### 4. Открыть в браузере

```
http://localhost:3000
```

### 5. Выбрать миссию и начать тестирование

---

## API для тестирования

### Создание песочницы

```bash
# Для GUI-миссии (уровень A)
curl -X POST http://localhost:8000/api/v1/sandbox/create \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "copy_file",
    "level": "A",
    "use_vnc": true
  }'

# Для CLI-миссии (уровень B)
curl -X POST http://localhost:8000/api/v1/sandbox/create \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "create_archive",
    "level": "B",
    "use_vnc": false
  }'
```

### Получение VNC URL

```bash
curl http://localhost:8000/api/v1/sandbox/copy_file/vnc
```

### Проверка миссии

```bash
curl -X POST http://localhost:8000/api/v1/grader/check \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "copy_file"
  }'
```

---

## Ожидаемые результаты

### Уровень A (GUI)
- ✅ VNC подключение работает
- ✅ XFCE Desktop загружается
- ✅ Файловый менеджер открывается
- ✅ Файлы можно копировать
- ✅ Настройки рабочего стола доступны

### Уровень B (CLI)
- ✅ Терминал доступен
- ✅ Команды выполняются
- ✅ Файлы создаются
- ✅ Архивы работают

### Уровень C (Admin)
- ✅ Sudo доступен
- ✅ Systemd работает
- ✅ Сервисы создаются
- ✅ Конфигурация применяется

---

## Известные ограничения

1. **VNC**: Первый запуск может занять 30-60 секунд
2. **XFCE**: Некоторые настройки требуют перезагрузки сессии
3. **Systemd**: В контейнере может работать не полностью
4. **Sudo**: Может требовать настройки в контейнере

---

## Следующие шаги

1. ✅ Протестировать каждую миссию вручную
2. ✅ Проверить работу grader
3. ✅ Добавить больше подсказок
4. ✅ Создать дополнительные миссии
5. ✅ Добавить скриншоты в документацию

