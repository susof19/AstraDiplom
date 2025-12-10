# Структура проекта

```
AstraDiplom/
├── backend/                    # Backend приложение (FastAPI)
│   ├── api/                   # API роуты
│   │   ├── main.py           # Главный файл приложения
│   │   └── routes/           # Роуты API
│   │       ├── missions.py   # Миссии
│   │       ├── sandbox.py   # Песочницы
│   │       ├── grader.py    # Проверка заданий
│   │       └── progress.py  # Прогресс и достижения
│   ├── sandbox/              # Управление песочницами
│   │   ├── container.py     # Контейнерная песочница
│   │   └── manager.py        # Менеджер песочниц
│   ├── grader/               # Проверка выполнения
│   │   └── checker.py       # Проверка миссий
│   ├── models/               # Модели данных
│   │   └── progress.py      # Прогресс пользователя
│   ├── config.py             # Конфигурация
│   └── requirements.txt      # Python зависимости
│
├── frontend/                  # Frontend приложение (React)
│   └── web/                  # Веб-приложение
│       ├── src/
│       │   ├── pages/        # Страницы
│       │   │   ├── Dashboard.jsx
│       │   │   ├── MissionList.jsx
│       │   │   └── MissionDetail.jsx
│       │   ├── components/   # Компоненты
│       │   │   ├── Layout.jsx
│       │   │   └── SandboxViewer.jsx
│       │   └── api/          # API клиент
│       │       └── missions.js
│       ├── public/           # Статические файлы
│       │   └── index.html    # HTML шаблон
│       ├── package.json      # Node.js зависимости (Create React App)
│       └── src/              # Исходный код
│
├── missions/                  # Определения миссий
│   ├── level_a/             # Уровень A (GUI)
│   │   ├── copy_file/
│   │   ├── create_shortcut/
│   │   ├── install_app/
│   │   ├── change_wallpaper/
│   │   └── organize_files/
│   ├── level_b/             # Уровень B (CLI)
│   │   ├── create_archive/
│   │   ├── find_process/
│   │   └── backup_script/
│   └── level_c/             # Уровень C (Админ)
│
├── images/                   # Docker образы
│   ├── Dockerfile.astra-gui # Образ с GUI
│   └── start-gui.sh         # Скрипт запуска GUI
│
├── docs/                     # Документация
│   ├── ARCHITECTURE.md      # Архитектура
│   ├── SETUP.md             # Установка
│   └── MISSIONS.md          # Создание миссий
│
├── scripts/                  # Вспомогательные скрипты
│   ├── start.sh             # Запуск приложения
│   └── build-image.sh      # Сборка образа
│
├── README.md                 # Главный README
├── QUICKSTART.md            # Быстрый старт
├── CONTRIBUTING.md          # Руководство по вкладу
└── LICENSE                  # Лицензия
```

## Ключевые компоненты

### Backend

- **API** (`backend/api/`): REST API для frontend
- **Sandbox** (`backend/sandbox/`): Управление контейнерами Podman
- **Grader** (`backend/grader/`): Проверка выполнения заданий
- **Models** (`backend/models/`): Модели данных (прогресс, достижения)

### Frontend

- **Pages**: Главная, список миссий, детали миссии
- **Components**: Layout, SandboxViewer (VNC/терминал)
- **API**: Клиент для взаимодействия с backend

### Missions

Каждая миссия - это директория с `mission.yaml`, содержащим:
- Метаданные (название, описание, сложность)
- Цели (objectives)
- Подсказки (hints)
- Проверки (checks) для grader'а

### Images

Dockerfile для создания образов Astra Linux с разными конфигурациями:
- GUI образ (уровень A): XFCE + VNC
- CLI образ (уровень B): Минимальный образ с терминалом
- Admin образ (уровень C): Полный образ с systemd

