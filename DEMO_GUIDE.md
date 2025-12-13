# Руководство для демонстрации на дипломе

Пошаговая инструкция для успешной демонстрации Astra Linux Training Simulator.

## 📋 Подготовка перед демонстрацией

### 1. Проверка системы

```bash
cd /путь/к/AstraDiplom

# Проверка готовности
cd scripts
./check-setup.sh
```

### 2. Создание образов

**Для CLI-миссий** (уровни B, C) - работает с базовым Astra Linux:
```bash
cd scripts
./create-astra-image.sh
```

**Для GUI-миссий** (уровень A) - используйте Debian 12:
```bash
cd scripts
./create-astra-image.sh --vnc
# Выберите вариант 2 (Debian 12)
```

### 3. Проверка образов

```bash
podman images | grep astra-linux
```

Должны быть:
- `localhost/astra-linux:se` (базовый)
- `localhost/astra-linux:vnc` (с VNC, опционально)

---

## 🚀 Запуск для демонстрации

### Вариант 1: Автоматический запуск (рекомендуется)

Создайте скрипт запуска:

```bash
cd /путь/к/AstraDiplom
cat > start-demo.sh << 'EOF'
#!/bin/bash
# Скрипт запуска для демонстрации

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Запуск Astra Linux Training Simulator для демонстрации"
echo "=========================================================="
echo ""

# Проверка образов
echo "📦 Проверка образов..."
if ! podman images | grep -q "astra-linux"; then
    echo "⚠️  Образы не найдены!"
    echo "Создайте образы командой:"
    echo "  cd scripts && ./create-astra-image.sh"
    exit 1
fi
echo "✅ Образы найдены"
echo ""

# Запуск Backend
echo "🔧 Запуск Backend..."
cd backend
source venv/bin/activate
python run.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend запущен (PID: $BACKEND_PID)"
cd ..

# Ожидание запуска Backend
echo "⏳ Ожидание запуска Backend..."
sleep 5

# Проверка Backend
if curl -s http://localhost:8000/api/v1/missions > /dev/null; then
    echo "✅ Backend готов"
else
    echo "⚠️  Backend не отвечает, но продолжаем..."
fi
echo ""

# Запуск Frontend
echo "🌐 Запуск Frontend..."
cd frontend/web
BROWSER=none npm start > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend запущен (PID: $FRONTEND_PID)"
cd ../..

# Ожидание запуска Frontend
echo "⏳ Ожидание запуска Frontend..."
sleep 10

echo ""
echo "=========================================================="
echo "✅ Система запущена и готова к демонстрации!"
echo ""
echo "📍 Адреса:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Логи:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 Для остановки:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   Или нажмите Ctrl+C и выполните:"
echo "   pkill -f 'python run.py'"
echo "   pkill -f 'npm start'"
echo ""
echo "🎓 Готово к демонстрации!"
echo ""

# Сохранить PIDs
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Открыть браузер (опционально)
read -p "Открыть браузер? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    xdg-open http://localhost:3000 2>/dev/null || \
    firefox http://localhost:3000 2>/dev/null || \
    chromium http://localhost:3000 2>/dev/null || \
    echo "Откройте вручную: http://localhost:3000"
fi

# Держать скрипт активным
echo "Нажмите Ctrl+C для остановки..."
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .backend.pid .frontend.pid; exit" INT TERM
wait
EOF

chmod +x start-demo.sh
```

**Запуск**:
```bash
./start-demo.sh
```

### Вариант 2: Ручной запуск

**Терминал 1 - Backend**:
```bash
cd backend
source venv/bin/activate
python run.py
```

**Терминал 2 - Frontend**:
```bash
cd frontend/web
npm start
```

**Терминал 3 - Мониторинг** (опционально):
```bash
watch -n 2 'podman ps'
```

---

## 🎯 Сценарий демонстрации

### Часть 1: Обзор системы (2-3 минуты)

1. **Открыть главную страницу**: http://localhost:3000
2. **Показать Dashboard**:
   - Количество миссий
   - Уровни сложности (A, B, C)
   - Прогресс пользователя

3. **Показать список миссий**:
   - Фильтрация по уровням
   - Описание миссий
   - Сложность и время

### Часть 2: Демонстрация CLI-миссии (5-7 минут)

**Рекомендуется**: Миссия "Создание архива" (уровень B)

1. **Выбрать миссию**:
   - Перейти в "Миссии" → Уровень B
   - Выбрать "Создание архива"

2. **Показать описание**:
   - Цели миссии
   - Подсказки
   - Критерии проверки

3. **Запустить песочницу**:
   - Нажать "Запустить песочницу"
   - Показать создание контейнера
   - Дождаться готовности

4. **Выполнить задание**:
   ```bash
   # В терминале песочницы
   ls -la documents/
   tar -czf backup.tar.gz documents/
   ls -la backup.tar.gz
   tar -tzf backup.tar.gz
   ```

5. **Проверить выполнение**:
   - Нажать "Проверить"
   - Показать результаты проверки
   - Объяснить систему оценки

### Часть 3: Демонстрация архитектуры (3-5 минут)

1. **Показать API** (опционально):
   - Открыть http://localhost:8000/docs
   - Показать endpoints
   - Продемонстрировать Swagger UI

2. **Показать контейнеры**:
   ```bash
   # В отдельном терминале
   podman ps
   podman images
   ```

3. **Объяснить изоляцию**:
   - Каждая миссия в отдельном контейнере
   - Rootless режим Podman
   - Автоматическая очистка

### Часть 4: Система проверки (2-3 минуты)

1. **Объяснить Grader**:
   - Автоматическая проверка
   - Типы проверок (файлы, команды, содержимое)
   - Система баллов

2. **Показать конфигурацию миссии**:
   ```bash
   cat missions/level_a/copy_file/mission.yaml
   ```

3. **Объяснить расширяемость**:
   - YAML конфигурация
   - Легко добавлять новые миссии
   - Гибкая система проверок

---

## 📊 API для демонстрации

### Создание песочницы

```bash
curl -X POST http://localhost:8000/api/v1/sandbox/create \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "copy_file",
    "level": "A",
    "use_vnc": true
  }'
```

### Проверка миссии

```bash
curl -X POST "http://localhost:8000/api/v1/grader/check/copy_file?level=A" \
  -H "Content-Type: application/json"
```

### Получение списка миссий

```bash
curl http://localhost:8000/api/v1/missions
```

---

## 🎓 Ключевые моменты для защиты

### Технологии

- **Backend**: FastAPI (Python 3.10+)
- **Frontend**: React 18
- **Контейнеризация**: Podman (rootless)
- **Изоляция**: Контейнеры Linux
- **Проверка**: Автоматический Grader

### Преимущества

1. **Безопасность**:
   - Изолированные песочницы
   - Rootless контейнеры
   - Нет доступа к хост-системе

2. **Масштабируемость**:
   - Легко добавлять миссии
   - YAML конфигурация
   - Модульная архитектура

3. **Удобство**:
   - Веб-интерфейс
   - Автоматическая проверка
   - Подсказки и обратная связь

4. **Совместимость**:
   - Работает на Astra Linux
   - Поддержка Windows (mock-режим)
   - Кроссплатформенность

### Возможности расширения

- Добавление новых уровней сложности
- Интеграция с LMS системами
- Мультипользовательский режим
- Система достижений и рейтингов
- Запись и воспроизведение сессий

---

## 🛑 Остановка после демонстрации

### Если использовали start-demo.sh

```bash
# Прочитать PIDs
BACKEND_PID=$(cat .backend.pid)
FRONTEND_PID=$(cat .frontend.pid)

# Остановить
kill $BACKEND_PID $FRONTEND_PID

# Или
pkill -f 'python run.py'
pkill -f 'npm start'
```

### Очистка контейнеров

```bash
# Остановить все контейнеры
podman stop $(podman ps -q)

# Удалить остановленные контейнеры
podman container prune -f

# Удалить неиспользуемые образы (опционально)
podman image prune -f
```

---

## 📝 Чек-лист перед демонстрацией

- [ ] Образы созданы (`podman images`)
- [ ] Backend запускается без ошибок
- [ ] Frontend открывается в браузере
- [ ] Список миссий загружается
- [ ] Можно создать песочницу
- [ ] Проверка миссии работает
- [ ] Интернет-соединение стабильно
- [ ] Презентация готова
- [ ] Запасной план (скриншоты/видео)

---

## 🆘 Решение проблем во время демонстрации

### Backend не запускается

```bash
# Проверить порт
netstat -tuln | grep 8000

# Убить процесс на порту
lsof -ti:8000 | xargs kill -9

# Перезапустить
cd backend && source venv/bin/activate && python run.py
```

### Frontend не открывается

```bash
# Проверить порт
netstat -tuln | grep 3000

# Очистить кэш
cd frontend/web
rm -rf node_modules/.cache
npm start
```

### Контейнер не создаётся

```bash
# Проверить Podman
podman info

# Проверить образы
podman images

# Пересоздать образ
cd scripts
./create-astra-image.sh
```

### Ошибка при сборке VNC образа

**Проблема**: `COPY start-vnc-simple.sh: no such file or directory`

**Решение**:
```bash
# Убедитесь, что файлы существуют
ls -la images/start-vnc*.sh

# Пересоберите из корня проекта
cd /путь/к/AstraDiplom
bash scripts/create-astra-image.sh --vnc

# Выберите вариант 2 (Debian 12) для полной функциональности
```

---

## 💡 Советы для успешной защиты

1. **Подготовьте запасной вариант**: Скриншоты или видео на случай технических проблем

2. **Протестируйте заранее**: Прогоните всю демонстрацию минимум 2-3 раза

3. **Подготовьте ответы** на вопросы:
   - Почему Podman, а не Docker?
   - Как обеспечивается безопасность?
   - Как добавить новую миссию?
   - Как система масштабируется?

4. **Держите открытыми**:
   - Терминал с логами
   - API документацию
   - Конфигурацию миссии

5. **Будьте готовы показать код**:
   - Grader (backend/grader/checker.py)
   - API (backend/api/routes/)
   - Конфигурация миссии (missions/)

---

## 🎉 Удачи на защите!

Вы создали полнофункциональный тренажёр с:
- ✅ Изолированными песочницами
- ✅ Автоматической проверкой
- ✅ Удобным веб-интерфейсом
- ✅ Расширяемой архитектурой

Это отличный проект! 🚀

