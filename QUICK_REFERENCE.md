# Быстрая справка - Astra Linux Training Simulator

## 🚀 Создание образов

```bash
cd scripts

# Базовый образ (CLI-миссии: уровни B, C)
./create-astra-image.sh

# Образ с VNC (GUI-миссии: уровень A)
./create-astra-image.sh --vnc
```

**Результат**:
- `localhost/astra-linux:se` - базовый
- `localhost/astra-linux:vnc` - с VNC

## 🔍 Проверка образов

```bash
# Список образов
podman images

# Тестовый запуск базового
podman run --rm -it localhost/astra-linux:se /bin/bash

# Тестовый запуск VNC
podman run -d -p 5900:5900 -p 6080:6080 localhost/astra-linux:vnc
# Откройте: http://localhost:6080/vnc.html
```

## 🔧 Решение проблем

### Образ не виден после создания

```bash
# Пересоздать без sudo (рекомендуется)
./create-astra-image.sh --vnc

# Или перенести существующий
./fix-podman-images.sh
```

### Ошибка "short-name did not resolve"

```bash
# Используйте полное имя
podman run localhost/astra-linux:se
```

## 📚 Документация

| Тема | Файл |
|------|------|
| Podman и образы | [docs/PODMAN_GUIDE.md](docs/PODMAN_GUIDE.md) |
| VNC и GUI | [docs/VNC_GUIDE.md](docs/VNC_GUIDE.md) |
| Решение проблем | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Скрипты | [scripts/README.md](scripts/README.md) |
| Установка на Astra | [docs/ASTRA_LINUX.md](docs/ASTRA_LINUX.md) |

## 💻 Запуск приложения

```bash
# Backend
cd backend
source venv/bin/activate
python run.py

# Frontend (в другом терминале)
cd frontend/web
npm start
```

Откройте: http://localhost:3000

## 🎮 Структура миссий

- **Уровень A** (GUI) - требует VNC образ
- **Уровень B** (CLI) - базовый образ
- **Уровень C** (Admin) - базовый образ

## 🔑 Учетные данные

**VNC**:
- Пользователь: `astrauser`
- Пароль: `astra123`

## 🆘 Помощь

```bash
# Справка по скрипту
./create-astra-image.sh --help

# Информация о Podman
podman info

# Логи контейнера
podman logs <container_name>
```

