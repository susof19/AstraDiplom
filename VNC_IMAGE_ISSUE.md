# Проблема с VNC образом Astra Linux

## 🐛 Проблема

При попытке создать VNC образ возникает ошибка:
```
E: Package 'xfce4' has no installation candidate
E: Unable to locate package xfce4-terminal
E: Unable to locate package xfce4-goodies
```

## 🔍 Причина

Базовый образ Astra Linux из реестра (`registry.astralinux.ru/library/astra/ubi18`) является **минимальным** и не содержит:
- GUI пакетов (XFCE, GNOME, KDE)
- TigerVNC Server
- X11 компонентов

Это нормально для серверного образа, но не подходит для GUI-миссий.

## ✅ Решения

### Решение 1: Использовать Debian 12 (рекомендуется для разработки)

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

### Решение 2: Использовать Mock-режим (для Windows)

```bash
# В backend/.env
MOCK_SANDBOX=true
```

**Преимущества**:
- ✅ Не требует Docker/Podman
- ✅ Быстрая разработка
- ✅ Тестирование логики без контейнеров

**Недостатки**:
- ⚠️ Нет реальной песочницы
- ⚠️ Только для разработки UI

### Решение 3: Использовать полный образ Astra Linux

Если у вас есть доступ к полному образу Astra Linux с GUI:

```bash
# Загрузить полный образ
podman pull <полный-образ-astra-linux>
podman tag <полный-образ> localhost/astra-linux:se

# Создать VNC образ на его основе
cd scripts
./create-astra-image.sh --vnc
```

### Решение 4: Использовать только CLI-миссии

Базовый образ отлично подходит для CLI-миссий (уровни B и C):

```bash
cd scripts
./create-astra-image.sh  # Без --vnc
```

Миссии уровня B и C не требуют GUI и будут работать отлично.

## 📊 Сравнение вариантов

| Вариант | GUI | Реальная песочница | Astra Linux | Сложность |
|---------|-----|-------------------|-------------|-----------|
| Debian 12 | ✅ | ✅ | ❌ | Низкая |
| Mock-режим | ✅ (эмуляция) | ❌ | ❌ | Очень низкая |
| Полный Astra | ✅ | ✅ | ✅ | Средняя |
| CLI-миссии | ❌ | ✅ | ✅ | Низкая |

## 🎯 Рекомендации

### Для разработки
→ **Debian 12** или **Mock-режим**

### Для продакшена
→ **Полный образ Astra Linux** с GUI пакетами

### Для обучения CLI
→ **Базовый образ** (без --vnc)

## 🚀 Быстрый старт с Debian 12

```bash
# 1. Создать образ с VNC на базе Debian
cd scripts
./create-astra-image.sh --vnc
# Выбрать вариант 2

# 2. Запустить backend
cd ../backend
source venv/bin/activate
python run.py

# 3. Запустить frontend
cd ../frontend/web
npm start

# 4. Открыть http://localhost:3000
```

## 📝 Примечания

- Упрощённая версия (вариант 1) создаёт образ без реального VNC, только для демонстрации структуры
- Для production использования требуется полный образ Astra Linux
- CLI-миссии (уровни B, C) работают с базовым образом без проблем
- GUI-миссии (уровень A) требуют полноценный GUI образ

## 🔗 Дополнительная информация

- [GETTING_STARTED.md](GETTING_STARTED.md) - Полное руководство
- [docs/VNC_GUIDE.md](docs/VNC_GUIDE.md) - Подробности о VNC
- [docs/WINDOWS_DEVELOPMENT.md](docs/WINDOWS_DEVELOPMENT.md) - Разработка на Windows

