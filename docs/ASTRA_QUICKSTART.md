# Быстрый старт на Astra Linux

## Автоматическая установка

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
6. ✅ Запустит проект (опционально)

## Что устанавливается

### Системные пакеты
- **Python 3.10+** - для backend
- **Node.js 18+** - для frontend
- **Podman** - для контейнеров
- **Git, curl** - вспомогательные инструменты

### Зависимости проекта
- Backend: все пакеты из `backend/requirements.txt`
- Frontend: все пакеты из `frontend/web/package.json`

## Запуск после установки

### Способ 1: Через скрипт
```bash
./start-trainer.sh
```

### Способ 2: Через ярлык на рабочем столе
Дважды кликните на "Astra Linux Trainer" на рабочем столе

### Способ 3: Вручную

**Терминал 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python run.py
```

**Терминал 2 - Frontend:**
```bash
cd frontend/web
npm start
```

## Установка образа Astra Linux

Для работы с реальными контейнерами нужно создать образ:

```bash
cd scripts
sudo ./create-astra-image.sh
```

Или используйте готовый образ, если он доступен.

## Troubleshooting

### Ошибка при установке пакетов

Если возникают проблемы с репозиториями:

```bash
# Обновить список пакетов
sudo apt-get update

# Проверить репозитории
cat /etc/apt/sources.list
```

### Node.js не устанавливается

Если NodeSource репозиторий недоступен, можно установить из репозиториев Astra:

```bash
sudo apt-get install nodejs npm
```

Или использовать nvm:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
```

### Podman не работает

```bash
# Проверить статус
podman info

# Настроить rootless режим
podman system migrate

# Если используется rootless-helper-astra
sudo apt-get install rootless-helper-astra
sudo systemctl start rootless-docker@$USER@0:0:0:0
```

### Проблемы с правами

Если скрипт не может создать ярлык:
```bash
chmod +x start-trainer.sh
chmod +x ~/Desktop/astra-trainer.desktop
```

## Ручная установка

Если автоматический скрипт не работает, см. [SETUP.md](SETUP.md) для детальных инструкций.

