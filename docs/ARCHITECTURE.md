# Архитектура Astra Linux Training Simulator

## Обзор

Тренажёр состоит из трёх основных компонентов:

1. **Backend (FastAPI)** - управление песочницами, проверка заданий, API
2. **Frontend (React)** - веб-интерфейс для пользователей
3. **Sandbox (Podman)** - изолированные контейнеры с Astra Linux

## Компоненты Backend

### Sandbox Manager

Управляет жизненным циклом контейнеров:
- Создание/удаление контейнеров для каждой миссии
- Автоматическая очистка истёкших песочниц
- Изоляция через rootless Podman

### Grader

Проверяет выполнение заданий:
- Загружает конфигурацию миссии (YAML)
- Выполняет проверки (файлы, команды, GUI-состояние)
- Возвращает результат с оценкой

### Progress System

Отслеживает прогресс пользователя:
- Завершённые миссии и оценки
- Достижения (achievements)
- Статистика по уровням

## Уровни сложности

### Уровень A (GUI-first)

- **Песочница**: Rootless Podman + XFCE + VNC
- **Интерфейс**: noVNC в браузере
- **Примеры миссий**: Копирование файлов, создание ярлыков, установка приложений

### Уровень B (CLI & Scripting)

- **Песочница**: Rootless Podman с терминалом
- **Интерфейс**: xterm.js в браузере
- **Примеры миссий**: Создание архивов, поиск процессов, bash-скрипты

### Уровень C (Администраторы)

- **Песочница**: LXC/systemd-nspawn или QEMU VM
- **Интерфейс**: Терминал + веб-панель управления
- **Примеры миссий**: Настройка systemd, firewall, кластеры

## Формат миссий

Миссии описываются в YAML:

```yaml
name: "Название миссии"
description: "Описание задания"
level: "A"  # A, B или C
difficulty: 1-5
estimated_time: 10  # минут

objectives:
  - "Цель 1"
  - "Цель 2"

hints:
  - "Подсказка 1"

checks:
  - name: "Проверка 1"
    type: "file_exists"
    path: "/path/to/file"
    points: 50
```

## Безопасность

- **Rootless контейнеры**: Все контейнеры запускаются без root-прав
- **Изоляция**: OverlayFS для отката изменений
- **Ограничения ресурсов**: CPU и память ограничены
- **Автоудаление**: Контейнеры удаляются после завершения

## API Endpoints

### Missions
- `GET /api/v1/missions` - список миссий
- `GET /api/v1/missions/{id}` - информация о миссии

### Sandbox
- `POST /api/v1/sandbox/create` - создать песочницу
- `GET /api/v1/sandbox/{mission_id}` - информация о песочнице
- `POST /api/v1/sandbox/{mission_id}/stop` - остановить
- `DELETE /api/v1/sandbox/{mission_id}` - удалить

### Grader
- `POST /api/v1/grader/check/{mission_id}` - проверить выполнение

### Progress
- `GET /api/v1/progress` - прогресс пользователя
- `POST /api/v1/progress/{mission_id}/complete` - отметить выполненной
- `GET /api/v1/progress/achievements` - достижения

