# Структура документации проекта

## 📁 Корень проекта

### Основные документы

- **README.md** - Главная страница проекта
- **GETTING_STARTED.md** - Полное руководство по началу работы
- **CONTRIBUTING.md** - Руководство по вкладу в проект

## 📁 docs/ - Техническая документация

### Установка и настройка
- **ASTRA_LINUX.md** - Установка на Astra Linux
- **WINDOWS_DEVELOPMENT.md** - Разработка на Windows
- **SETUP.md** - Детальная настройка

### Компоненты системы
- **PODMAN_GUIDE.md** - Работа с Podman и создание образов
- **VNC_GUIDE.md** - VNC для GUI-миссий
- **TROUBLESHOOTING.md** - Решение проблем

### Архитектура
- **ARCHITECTURE.md** - Архитектура системы
- **MISSIONS.md** - Создание миссий

## 📁 scripts/ - Документация скриптов

- **README.md** - Описание всех скриптов

## Что было удалено

### Консолидированные документы
- ❌ QUICK_REFERENCE.md → GETTING_STARTED.md
- ❌ QUICKSTART.md → GETTING_STARTED.md
- ❌ MISSIONS_TESTING_GUIDE.md → GETTING_STARTED.md
- ❌ TROUBLESHOOTING_IMAGE_BUILD.md → GETTING_STARTED.md

### Временные отчёты
- ❌ CLEANUP_SUMMARY.md
- ❌ PROJECT_STRUCTURE.md
- ❌ IMPLEMENTATION_STATUS.md

## Итого

**Было**: 14+ MD файлов  
**Стало**: 3 в корне + 8 в docs/ + 1 в scripts/ = **12 файлов**

**Сокращение**: ~15%  
**Улучшение**: Вся информация логично организована и легко находится

## Навигация

### Я новичок, с чего начать?
→ **GETTING_STARTED.md**

### Как установить на Astra Linux?
→ **docs/ASTRA_LINUX.md**

### Как создать образы?
→ **GETTING_STARTED.md** (раздел "Создание образов")  
→ **docs/PODMAN_GUIDE.md** (подробности)

### Как работает VNC?
→ **docs/VNC_GUIDE.md**

### Возникла проблема
→ **GETTING_STARTED.md** (раздел "Решение проблем")  
→ **docs/TROUBLESHOOTING.md**

### Как создать миссию?
→ **docs/MISSIONS.md**

### Хочу внести вклад
→ **CONTRIBUTING.md**

### Как работает система?
→ **docs/ARCHITECTURE.md**

